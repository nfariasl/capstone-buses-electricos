"""Heurística constructiva con calendario compartido; no prueba optimalidad."""
import math
import os
import numpy as np


def _leer_entorno(nombre, omision):
    """Batería, reserva y consumo para la sensibilidad (mismas variables que metodo_hibrido/energia.py)."""
    valor = float(os.environ.get(nombre, omision))
    if valor <= 0:
        raise ValueError(f'{nombre} debe ser positivo: {valor}')
    return valor


BATERIA = _leer_entorno('BATERIA_KWH', 350.)
MINIMO = _leer_entorno('RESERVA_KWH', 35.)
CONSUMO = _leer_entorno('CONSUMO_KWH_KM', 1.4)
if MINIMO >= BATERIA:
    raise ValueError(f'La reserva ({MINIMO}) debe ser menor que la batería ({BATERIA})')
BLOQUE, MAX_CARGA = 300, 15.
EPS = 1e-7

def precio(second, tariffs):
    hour = (second % 86400)/3600
    return next(p for a, b, p in tariffs if a <= hour < b)

class Calendario:
    """Ocupación física a segundo entero y conexiones por bloque de cinco minutos."""
    def __init__(self, physical, plugs, t0, horizon):
        self.physical, self.plugs = physical, plugs
        self.t0, self.horizon = t0, horizon
        self.presence = {e: np.zeros(horizon-t0, dtype=np.int32) for e in physical}
        self.connections = {e: {} for e in physical}

    def libre(self, e, start, end, charging=False):
        if start < self.t0 or end > self.horizon or end < start:
            return False
        if end > start and np.max(self.presence[e][start-self.t0:end-self.t0]) >= self.physical[e]:
            return False
        if charging:
            return all(self.connections[e].get(t, 0) < self.plugs[e] for t in range(start, end, BLOQUE))
        return True

    def reservar(self, e, start, end, charging=False):
        if not self.libre(e, start, end, charging):
            raise AssertionError('Reserva que excede capacidad')
        self.presence[e][start-self.t0:end-self.t0] += 1
        if charging:
            for t in range(start, end, BLOQUE):
                self.connections[e][t] = self.connections[e].get(t, 0)+1

def actividad(kind, origin, target, start, end, km=0., q=0., trip=''):
    return dict(tipo=kind, origen=origin, destino=target, inicio_s=int(start), fin_s=int(end),
                distancia_km=float(km), carga_kwh=float(q), corrida_id=trip)

def agregar_viaje(result, origin, target, start, distances):
    km, duration = distances[origin, target]
    if duration or km:
        result.append(actividad('vacio', origin, target, start, start+duration, km))
    return start+duration

def esperar(result, loc, start, end):
    if end > start:
        result.append(actividad('espera', loc, loc, start, end))

def mejor_recarga(origin, target, earliest, latest, soc, need_after, distances, calendar, tariffs):
    """Busca corridas de bloques libres en los cinco E. Mayor ganancia neta; luego costo."""
    direct = distances[origin, target][0]
    best = None
    for e in sorted(calendar.physical):
        if (origin, e) not in distances or (e, target) not in distances:
            continue
        km1, dt1 = distances[origin, e]
        km2, dt2 = distances[e, target]
        arrival_soc = soc-CONSUMO*km1
        if arrival_soc < MINIMO-EPS:
            continue
        first = math.ceil((earliest+dt1)/BLOQUE)*BLOQUE
        last = math.floor((latest-dt2)/BLOQUE)*BLOQUE
        room = BATERIA-arrival_soc
        need = max(0., need_after+CONSUMO*km2-arrival_soc)
        run = []
        for t in range(first, last, BLOQUE):
            if calendar.libre(e, t, t+BLOQUE, True):
                run.append(t)
            else:
                run = []
            if not run:
                continue
            n = min(len(run), max(1, math.ceil(min(room, need)/MAX_CARGA)))
            start, end = run[-n], t+BLOQUE
            q = min(room, need, n*MAX_CARGA)
            gain = q-CONSUMO*(km1+km2-direct)
            if gain <= EPS:
                continue
            energy_cost = sum(min(MAX_CARGA, max(0., q-i*MAX_CARGA))*precio(s, tariffs)
                              for i, s in enumerate(range(start, end, BLOQUE)))
            score = (-gain, energy_cost+.5*(km1+km2-direct)+5, start, e)
            if best is None or score < best['score']:
                best = dict(e=e, start=start, end=end, q=q, km1=km1, km2=km2,
                            dt1=dt1, dt2=dt2, score=score)
    return best

def construir(chains, lookup, distances, starts, physical, plugs, tariffs, t0, horizon):
    calendar = Calendario(physical, plugs, t0, horizon)
    schedules, splits = [], []
    chains = sorted(chains, key=lambda c: (lookup[c['corridas'][0]]['inicio_s'], -len(c['corridas']), c['id']))
    for chain in chains:
        trips = [lookup[i] for i in chain['corridas']]
        offset = 0
        while offset < len(trips):
            first = trips[offset]
            origin = 'S:'+first['inicio_stop_id']
            final_stop = 'S:'+first['fin_stop_id']
            return_km = min(distances[final_stop, t][0] for t in starts)
            candidates = [t for t in starts if t0+distances[t, origin][1] <= first['inicio_s']
                          and CONSUMO*(distances[t, origin][0]+first['distancia_servicio_km']+return_km) <= BATERIA-MINIMO+EPS]
            if not candidates:
                raise RuntimeError(f"Heurística sin solución: {first['corrida_id']} no admite salida y retorno conservador a T con un bus nuevo. No prueba infactibilidad del modelo completo.")
            initial = min(candidates, key=lambda t: (distances[t, origin][0], t))
            acts = []
            departure = first['inicio_s']-distances[initial, origin][1]
            esperar(acts, initial, t0, departure)
            arrival = agregar_viaje(acts, initial, origin, departure, distances)
            soc = BATERIA-CONSUMO*distances[initial, origin][0]
            current, now = origin, arrival
            covered = []
            # Sufijo sin recargas: referencia para anticipar necesidad, no compromiso futuro.
            suffix = [0.]*(len(trips)+1)
            suffix[-1] = CONSUMO*min(distances['S:'+trips[-1]['fin_stop_id'], t][0] for t in starts)+MINIMO
            for j in range(len(trips)-1, offset-1, -1):
                transfer = 0 if j == len(trips)-1 else distances['S:'+trips[j]['fin_stop_id'], 'S:'+trips[j+1]['inicio_stop_id']][0]
                suffix[j] = CONSUMO*(trips[j]['distancia_servicio_km']+transfer)+suffix[j+1]
            j = offset
            while j < len(trips):
                trip = trips[j]
                target, endstop = 'S:'+trip['inicio_stop_id'], 'S:'+trip['fin_stop_id']
                km, dt = distances[current, target]
                reserve = MINIMO+CONSUMO*(trip['distancia_servicio_km']+min(distances[endstop, t][0] for t in starts))
                if now+dt > trip['inicio_s']:
                    break
                charge = None
                if covered and soc-CONSUMO*km < suffix[j]-EPS:
                    charge = mejor_recarga(current, target, now, trip['inicio_s'], soc, suffix[j], distances, calendar, tariffs)
                predicted = soc-CONSUMO*km if charge is None else soc-CONSUMO*(charge['km1']+charge['km2'])+charge['q']
                if predicted < reserve-EPS:
                    break
                if charge:
                    c = charge
                    esperar(acts, current, now, c['start']-c['dt1'])
                    agregar_viaje(acts, current, c['e'], c['start']-c['dt1'], distances)
                    for n, s in enumerate(range(c['start'], c['end'], BLOQUE)):
                        q = min(MAX_CARGA, max(0., c['q']-n*MAX_CARGA))
                        acts.append(actividad('carga', c['e'], c['e'], s, s+BLOQUE, q=q))
                    calendar.reservar(c['e'], c['start'], c['end'], True)
                    arrival = agregar_viaje(acts, c['e'], target, c['end'], distances)
                else:
                    arrival = agregar_viaje(acts, current, target, now, distances)
                esperar(acts, target, arrival, trip['inicio_s'])
                acts.append(actividad('servicio', target, endstop, trip['inicio_s'], trip['fin_s'], trip['distancia_servicio_km'], trip=trip['corrida_id']))
                soc = predicted-CONSUMO*trip['distancia_servicio_km']
                current, now = endstop, trip['fin_s']
                covered.append(trip['corrida_id'])
                j += 1
            if not covered:
                raise AssertionError('Bus nuevo sin servicio pese al control de salida')
            ends = []
            for t in starts+sorted(physical):
                km, dt = distances[current, t]
                if soc-CONSUMO*km >= MINIMO-EPS and now+dt <= horizon:
                    if t in physical and not calendar.libre(t, now+dt, horizon):
                        continue
                    ends.append(t)
            if not ends:
                raise AssertionError('Se perdió la reserva para retorno a terminal común')
            final = min(ends, key=lambda t: (distances[current, t][0], t))
            finish = agregar_viaje(acts, current, final, now, distances)
            esperar(acts, final, finish, horizon)
            if final in physical:
                calendar.reservar(final, finish, horizon)
            schedules.append(dict(bus_id=f'B{len(schedules)+1:05d}', cadena_fase2=chain['id'],
                                  sector_id=first['sector_id'], terminal_inicial=initial, terminal_final=final,
                                  corridas=covered, actividades=acts))
            if j < len(trips):
                splits.append(dict(cadena_fase2=chain['id'], ultima_corrida=covered[-1],
                                   siguiente_corrida=trips[j]['corrida_id'], motivo='Reserva energética o enlace no alcanzable por la heurística'))
            offset = j
    return schedules, splits
