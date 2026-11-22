"""Caso base cronológico independiente. Python 3.10+, biblioteca estándar."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

from metodo_hibrido.verificar import verificar
from metodo_hibrido.energia import BATERIA, CONSUMO, RESERVA

BATTERY, RESERVE, RATE = BATERIA, RESERVA, CONSUMO
BLOCK, PER_BLOCK, EPS = 300, 15.0, 1e-7


class InputError(ValueError):
    pass


def read_csv(path):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))


def write_csv(path, rows):
    with Path(path).open('w', encoding='utf-8-sig', newline='') as stream:
        if rows:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)


def tariff(second, prices):
    hour = second % 86400 / 3600
    return next(p for start, end, p in prices if start <= hour < end)


class Calendar:
    """Intervalos [inicio, fin); calendarios separados para presencia y conexión."""

    def __init__(self, physical, plugs, t0, horizon):
        self.physical, self.plugs = physical, plugs
        self.t0, self.horizon = t0, horizon
        self.presence = {e: [] for e in physical}
        self.connections = {e: [] for e in physical}

    @staticmethod
    def fits(intervals, start, end, limit):
        if start == end:
            return True
        changes = Counter({start: 1, end: -1})
        for a, b in intervals:
            if a < end and start < b:
                changes[max(a, start)] += 1
                changes[min(b, end)] -= 1
        occupation = 0
        for point in sorted(changes):
            occupation += changes[point]
            if occupation > limit:
                return False
        return occupation == 0

    def free(self, e, start, end, charging=False):
        return (self.t0 <= start <= end <= self.horizon
                and self.fits(self.presence[e], start, end, self.physical[e])
                and (not charging or self.fits(self.connections[e], start, end, self.plugs[e])))

    def reserve(self, e, start, end, charging=False):
        if not self.free(e, start, end, charging):
            raise RuntimeError('Intento de reserva incompatible')
        if end > start:
            self.presence[e].append((start, end))
            if charging:
                self.connections[e].append((start, end))


def activity(kind, origin, target, start, end, km=0.0, q=0.0, trip=''):
    return dict(tipo=kind, origen=origin, destino=target, inicio_s=int(start), fin_s=int(end),
                distancia_km=float(km), carga_kwh=float(q), corrida_id=trip)


def wait(acts, loc, start, end):
    if end < start:
        raise RuntimeError('Espera negativa')
    if end > start:
        acts.append(activity('espera', loc, loc, start, end))


def move(acts, origin, target, start, distances):
    km, duration = distances[origin, target]
    if duration:
        acts.append(activity('vacio', origin, target, start, start + duration, km))
    elif origin != target:
        raise InputError(f'Conexión de duración cero entre IDs distintos: {origin}, {target}; revisar datos')
    return start + duration


def reachable_return(trip, starts, distances, horizon):
    stop = 'S:' + trip['fin_stop_id']
    options = [(distances[stop, t][0], t) for t in starts
               if distances.get((stop, t)) is not None
               and trip['fin_s'] + distances[stop, t][1] <= horizon]
    return min(options) if options else None


def charge_options(bus, target, deadline, required, distances, calendar, prices, max_km=math.inf):
    """Una visita; carga mínima para la siguiente corrida y retorno a T."""
    options = []
    for e in sorted(calendar.physical):
        leg1 = distances.get((bus['loc'], e))
        leg2 = distances.get((e, target))
        if leg1 is None or leg2 is None:
            continue
        km1, dt1 = leg1
        km2, dt2 = leg2
        if km1 + km2 > max_km:
            continue  # No puede ganar al candidato actual bajo la regla de menor distancia.
        arrival_soc = bus['soc'] - RATE * km1
        if arrival_soc < RESERVE - EPS:
            continue
        q = max(0.0, required + RATE * km2 - arrival_soc)
        if q <= EPS or arrival_soc + q > BATTERY + EPS:
            continue
        n = math.ceil(max(0.0, q - EPS) / PER_BLOCK)
        first = math.ceil((bus['now'] + dt1) / BLOCK) * BLOCK
        last = math.floor((deadline - dt2) / BLOCK) * BLOCK
        for start in range(first, last - n * BLOCK + 1, BLOCK):
            end = start + n * BLOCK
            if not calendar.free(e, start, end, True):
                continue
            cost = sum(min(PER_BLOCK, max(0.0, q - i * PER_BLOCK)) * tariff(start+i*BLOCK, prices)
                       for i in range(n))
            options.append(dict(kind='charge', km=km1+km2, q=q, cost=.5*(km1+km2)+cost+5,
                                e=e, start=start, end=end, dt1=dt1, km1=km1, km2=km2,
                                soc=arrival_soc+q-RATE*km2))
    return options


DAY_TYPES = ('L', 'S', 'D')  # laboral, sábado, domingo o festivo


def validate_inputs(trips, distances, starts, physical, plugs, prices, t0, horizon):
    if not trips or t0 >= horizon:
        raise InputError('Instancia vacía u horizonte inválido')
    ids = [t['corrida_id'] for t in trips]
    if len(set(ids)) != len(ids):
        raise InputError('Identificadores de corridas duplicados')
    if not starts or set(physical) != set(plugs):
        raise InputError('Instalaciones incompletas')
    if any(not isinstance(v, int) or v < 0 for v in list(physical.values())+list(plugs.values())):
        raise InputError('Capacidades inválidas')
    last = 0
    for a, b, price in sorted(prices):
        if a != last or b <= a or price < 0 or not math.isfinite(price):
            raise InputError('Tarifas con huecos, solapamientos o valores inválidos')
        if (a*3600) % BLOCK or (b*3600) % BLOCK:
            raise InputError('Las tarifas deben cambiar en fronteras de bloques')
        last = b
    if last != 24:
        raise InputError('Las tarifas deben cubrir 24 horas')
    origins = {'S:'+t['inicio_stop_id'] for t in trips}
    ends = {'S:'+t['fin_stop_id'] for t in trips}
    needed = {(t, o) for t in starts for o in origins}
    needed |= {(a, t) for a in ends for t in starts}
    needed |= {(a, o) for a in ends for o in origins}
    needed |= {(a, e) for a in ends for e in physical}
    needed |= {(e, o) for e in physical for o in origins}
    absent = sorted(needed - set(distances))
    if absent:
        raise InputError(f'Faltan {len(absent)} pares de distancia (no equivalen a sin camino): {absent[:8]}')
    for pair, value in distances.items():
        if value is None:  # Conexión declarada expresamente inalcanzable.
            continue
        km, duration = value
        if not math.isfinite(km) or km < 0 or duration != math.ceil(km*3600/18):
            raise InputError(f'Distancia o duración inválida: {pair}')
        if pair[0] != pair[1] and duration == 0:
            raise InputError(f'Normalizar extremos coincidentes antes de ejecutar: {pair}')
    services = {trip.get('service_id', 'L') for trip in trips}
    if len(services) != 1 or not services <= set(DAY_TYPES):
        raise InputError(f'La instancia debe tener un solo tipo de día (L, S o D): {sorted(services)}')
    for trip in trips:
        if not t0 <= trip['inicio_s'] < trip['fin_s'] <= horizon:
            raise InputError(f'Corrida fuera del escenario: {trip["corrida_id"]}')
        km = trip['distancia_servicio_km']
        if not math.isfinite(km) or km < 0:
            raise InputError('Longitud de servicio inválida')


def solve(trips, distances, starts, physical, plugs, prices, t0, horizon, progress=None):
    validate_inputs(trips, distances, starts, physical, plugs, prices, t0, horizon)
    calendar = Calendar(physical, plugs, t0, horizon)
    buses, decisions = [], []
    for trip_number, trip in enumerate(sorted(trips, key=lambda t: (t['inicio_s'], t['corrida_id'])), 1):
        target, endstop = 'S:'+trip['inicio_stop_id'], 'S:'+trip['fin_stop_id']
        ret = reachable_return(trip, starts, distances, horizon)
        if ret is None:
            raise RuntimeError(f'Fallo del caso base: {trip["corrida_id"]} no tiene retorno directo a T')
        required = RESERVE + RATE*(trip['distancia_servicio_km']+ret[0])
        options = []
        needing_charge = []
        for bus in buses:
            if bus['sector_id'] != trip['sector_id'] or bus['now'] > trip['inicio_s']:
                continue
            direct = distances.get((bus['loc'], target))
            if direct is not None and bus['now']+direct[1] <= trip['inicio_s'] and bus['soc']-RATE*direct[0] >= required-EPS:
                options.append((bus, dict(kind='direct', km=direct[0], q=0.0, cost=.5*direct[0],
                                          soc=bus['soc']-RATE*direct[0], start=bus['now'], e='')))
            else:
                needing_charge.append(bus)
        max_km = min((c['km'] for _, c in options), default=math.inf)
        for bus in needing_charge:
            candidates = charge_options(bus, target, trip['inicio_s'], required, distances, calendar, prices, max_km)
            options.extend((bus, c) for c in candidates)
            if candidates:
                max_km = min(max_km, min(c['km'] for c in candidates))
        if options:
            bus, option = min(options, key=lambda x: (x[1]['km'], x[1]['cost'], x[0]['bus_id'], x[1]['start'], x[1]['e']))
            reason = 'bus_existente_con_recarga' if option['kind'] == 'charge' else 'bus_existente_directo'
        else:
            initial = [(distances[t, target][0], t) for t in starts
                       if distances.get((t, target)) is not None
                       and t0+distances[t, target][1] <= trip['inicio_s']
                       and BATTERY-RATE*distances[t, target][0] >= required-EPS]
            if not initial:
                raise RuntimeError(f'Fallo heurístico en {trip["corrida_id"]}; no prueba infactibilidad del problema')
            km, terminal = min(initial)
            bus = dict(bus_id=f'B{len(buses)+1:05d}', cadena_fase2='CASO_BASE', sector_id=trip['sector_id'],
                       terminal_inicial=terminal, corridas=[], actividades=[], loc=terminal, now=t0, soc=BATTERY)
            buses.append(bus)
            departure = trip['inicio_s']-distances[terminal, target][1]
            option = dict(kind='direct', km=km, q=0.0, cost=.5*km, soc=BATTERY-RATE*km, start=departure, e='')
            reason = 'bus_nuevo'
        acts = bus['actividades']
        if option['kind'] == 'charge':
            wait(acts, bus['loc'], bus['now'], option['start']-option['dt1'])
            move(acts, bus['loc'], option['e'], option['start']-option['dt1'], distances)
            for i, second in enumerate(range(option['start'], option['end'], BLOCK)):
                q = min(PER_BLOCK, max(0.0, option['q']-i*PER_BLOCK))
                acts.append(activity('carga', option['e'], option['e'], second, second+BLOCK, q=q))
            calendar.reserve(option['e'], option['start'], option['end'], True)
            arrival = move(acts, option['e'], target, option['end'], distances)
        else:
            wait(acts, bus['loc'], bus['now'], option['start'])
            arrival = move(acts, bus['loc'], target, option['start'], distances)
        wait(acts, target, arrival, trip['inicio_s'])
        acts.append(activity('servicio', target, endstop, trip['inicio_s'], trip['fin_s'],
                             trip['distancia_servicio_km'], trip=trip['corrida_id']))
        bus['soc'] = option['soc']-RATE*trip['distancia_servicio_km']
        bus['loc'], bus['now'] = endstop, trip['fin_s']
        bus['corridas'].append(trip['corrida_id'])
        decisions.append(dict(corrida_id=trip['corrida_id'], bus_id=bus['bus_id'], decision=reason,
                              km_vacio_conexion=option['km'], carga_kwh=option['q'],
                              energia_despues_servicio_kwh=bus['soc']))
        if progress and (trip_number % 1000 == 0 or trip_number == len(trips)):
            progress(trip_number, len(trips), len(buses))
    # Todas las recargas ya están reservadas: el estacionamiento no las desplaza.
    for bus in sorted(buses, key=lambda b: (b['now'], b['bus_id'])):
        options = []
        for terminal in starts+sorted(physical):
            leg = distances.get((bus['loc'], terminal))
            if leg is None:
                continue
            km, duration = leg
            if bus['soc']-RATE*km < RESERVE-EPS or bus['now']+duration > horizon:
                continue
            if terminal in physical and not calendar.free(terminal, bus['now']+duration, horizon):
                continue
            options.append((km, terminal))
        if not options:
            raise RuntimeError('No se conservó un retorno factible')
        km, terminal = min(options)
        finish = move(bus['actividades'], bus['loc'], terminal, bus['now'], distances)
        wait(bus['actividades'], terminal, finish, horizon)
        if terminal in physical:
            calendar.reserve(terminal, finish, horizon)
        bus['terminal_final'] = terminal
        for key in ('soc', 'loc', 'now'):
            bus.pop(key)
    summary, journeys, activities = verificar(buses, trips, distances, starts, physical, plugs, prices, t0, horizon)
    summary.update(metodo='Asignación cronológica por menor distancia vacía', optimalidad_demostrada=False,
                   km_servicio=sum(j['km_servicio'] for j in journeys), km_vacio=sum(j['km_vacio'] for j in journeys),
                   energia_consumida_kwh=RATE*summary['km'],
                   deficit_reposicion_kwh=sum(BATTERY-j['energia_final_kwh'] for j in journeys))
    summary['porcentaje_km_vacio'] = 100*summary['km_vacio']/summary['km'] if summary['km'] else 0
    return summary, journeys, activities, decisions, buses


def load_instance(folder):
    folder = Path(folder)
    spec = json.loads((folder/'escenario.json').read_text(encoding='utf-8-sig'))
    fixed = dict(bateria_kwh=BATERIA, reserva_kwh=RESERVA, consumo_kwh_km=1.4, velocidad_vacio_kmh=18,
                 potencia_kw=180, bloque_s=300, costo_bus=250, costo_km=.5, costo_sesion=5)
    for key, value in spec.get('parametros', {}).items():
        if key in fixed and value != fixed[key]:
            raise InputError(f'Este código usa {key}={fixed[key]}; el escenario declara {value}')
    trips = read_csv(folder/'corridas.csv')
    for t in trips:
        t['inicio_s'], t['fin_s'] = int(t['inicio_s']), int(t['fin_s'])
        t['distancia_servicio_km'] = float(t['distancia_servicio_km'])
    distances = {}
    for r in read_csv(folder/'distancias.csv'):
        key = r['origen_id'], r['destino_id']
        if key in distances:
            raise InputError(f'Par duplicado: {key}')
        if r.get('estado') == 'sin_camino':
            distances[key] = None
        elif r['distancia_km']:
            km = float(r['distancia_km'])
            distances[key] = km, math.ceil(km*3600/18)
        else:
            raise InputError(f'Distancia vacía sin declaración de inalcanzabilidad: {key}')
    return trips, distances, spec['terminales_espera'], spec['capacidad_fisica'], spec['conexiones'], spec['tarifas'], spec['inicio_horizonte_s'], spec['fin_horizonte_s']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--instancia', type=Path, required=True)
    parser.add_argument('--salida', type=Path, required=True)
    args = parser.parse_args()
    args.salida.mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    try:
        summary, journeys, activities, decisions, buses = solve(*load_instance(args.instancia),
            progress=lambda n, total, buses: print(f'Asignadas {n}/{total}; buses {buses}', file=sys.stderr, flush=True))
    except (InputError, RuntimeError, AssertionError, FileNotFoundError) as exc:
        (args.salida/'fallo.json').write_text(json.dumps(dict(estado='sin_solucion_validada', error=str(exc)),
                                                        ensure_ascii=False, indent=2), encoding='utf-8')
        raise SystemExit(str(exc))
    summary['tiempo_total_s'] = time.perf_counter()-start
    summary['huellas_entrada_sha256'] = {name: hashlib.sha256((args.instancia/name).read_bytes()).hexdigest()
                                       for name in ('escenario.json', 'corridas.csv', 'distancias.csv')}
    for name, rows in [('jornadas', journeys), ('actividades', activities), ('decisiones', decisions),
                       ('recargas', [a for a in activities if a['tipo'] == 'carga'])]:
        write_csv(args.salida/(name+'.csv'), rows)
    (args.salida/'planes.json').write_text(json.dumps(buses, ensure_ascii=False, indent=2), encoding='utf-8')
    (args.salida/'resumen.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
