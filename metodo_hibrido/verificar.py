"""Auditoría independiente de las actividades exportadas (no usa el calendario constructor)."""
from collections import Counter, defaultdict
import math
from metodo_hibrido.energia import BATERIA, RESERVA

def verificar(schedules, trips, distances, starts, physical, plugs, tariffs, t0, horizon):
    expected = {t['corrida_id']: t for t in trips}
    coverage = Counter()
    presence, connections = defaultdict(list), defaultdict(list)
    journeys, activities = [], []
    total_km = total_q = total_energy_cost = 0.
    sessions = 0
    def check(condition, message):
        if not condition:
            raise AssertionError(message)
    def capacity(events):
        changes = defaultdict(int)
        for start, end in events:
            changes[start] += 1
            changes[end] -= 1
        value = peak = 0
        for t in sorted(changes):
            value += changes[t]
            peak = max(peak, value)
        check(value == 0, 'Ocupación sin cierre')
        return peak
    check(len({s['bus_id'] for s in schedules}) == len(schedules), 'Identificador de bus duplicado')
    for bus in schedules:
        soc, lowest = BATERIA, BATERIA
        loc, time = bus['terminal_inicial'], t0
        check(loc in starts, 'Salida fuera de los cuatro T')
        km_service = km_empty = q_sum = energy_cost = 0.
        bus_sessions = 0
        previous = None
        bus_covered = []
        for order, a in enumerate(bus['actividades'], 1):
            s, f = a['inicio_s'], a['fin_s']
            check(isinstance(s, int) and isinstance(f, int) and f > s, 'Duración no positiva o no entera')
            check(s == time and a['origen'] == loc, f"Discontinuidad {bus['bus_id']} actividad {order}")
            check(f <= horizon, 'Actividad fuera del horizonte')
            km, q = a['distancia_km'], a['carga_kwh']
            check(math.isfinite(km) and math.isfinite(q) and km >= 0 and q >= 0, 'Parámetro no válido')
            before = soc
            if a['tipo'] == 'servicio':
                check(a['corrida_id'] in expected, 'Servicio desconocido')
                t = expected[a['corrida_id']]
                check((s, f, a['origen'], a['destino']) == (t['inicio_s'], t['fin_s'], 'S:'+t['inicio_stop_id'], 'S:'+t['fin_stop_id']), 'Servicio modificado')
                check(t['sector_id'] == bus['sector_id'], 'Servicio en otro sector')
                check(abs(km-t['distancia_servicio_km']) < 1e-6 and q == 0, 'Distancia de servicio incorrecta')
                coverage[a['corrida_id']] += 1
                bus_covered.append(a['corrida_id'])
                km_service += km
                soc -= 1.4*km
            elif a['tipo'] == 'vacio':
                d, duration = distances[a['origen'], a['destino']]
                check(abs(km-d) < 1e-6 and f-s == duration and q == 0, 'Traslado incorrecto')
                km_empty += km
                soc -= 1.4*km
            elif a['tipo'] in ('carga', 'espera'):
                check(a['origen'] == a['destino'] and km == 0, 'Actividad estacionaria con movimiento')
                if a['origen'] in physical:
                    presence[a['origen']].append((s, f))
                if a['tipo'] == 'carga':
                    check(a['origen'] in physical and s % 300 == 0 and f-s == 300 and q <= 15+1e-7, 'Recarga inválida')
                    connections[a['origen']].append((s, f))
                    if previous is None or previous['tipo'] != 'carga' or previous['destino'] != a['origen'] or previous['fin_s'] != s:
                        bus_sessions += 1
                    hour = (s % 86400)/3600
                    price = next(p for lo, hi, p in tariffs if lo <= hour < hi)
                    energy_cost += q*price
                    q_sum += q
                    soc += q
                else:
                    check(q == 0, 'Carga en una espera')
            else:
                raise AssertionError('Actividad desconocida')
            check(RESERVA-1e-6 <= soc <= BATERIA+1e-6, f"SOC inválido {bus['bus_id']} {order}: {soc}")
            lowest = min(lowest, soc)
            activities.append(dict(bus_id=bus['bus_id'], orden=order, **a, energia_inicial_kwh=before, energia_final_kwh=soc))
            loc, time, previous = a['destino'], f, a
        check(bus_covered == bus['corridas'] and bus_covered, 'Lista de corridas inconsistente')
        check(time == horizon and loc == bus['terminal_final'] and loc in set(starts)|set(physical), 'Final o estacionamiento incompleto')
        check(abs(BATERIA+q_sum-1.4*(km_service+km_empty)-soc) < 1e-5, 'Balance energético incorrecto')
        cost = 250+.5*(km_service+km_empty)+energy_cost+5*bus_sessions
        journeys.append(dict(bus_id=bus['bus_id'], cadena_fase2=bus['cadena_fase2'], sector_id=bus['sector_id'],
                             terminal_inicial=bus['terminal_inicial'], terminal_final=loc, corridas=len(bus_covered),
                             km_servicio=km_service, km_vacio=km_empty, carga_kwh=q_sum, sesiones=bus_sessions,
                             energia_minima_kwh=lowest, energia_final_kwh=soc, costo_usd=cost))
        total_km += km_service+km_empty
        total_q += q_sum
        total_energy_cost += energy_cost
        sessions += bus_sessions
    check(set(coverage) == set(expected) and all(n == 1 for n in coverage.values()), 'Cobertura incompleta o duplicada')
    peaks = {}
    for e in physical:
        p, c = capacity(presence[e]), capacity(connections[e])
        check(p <= physical[e] and c <= plugs[e], 'Capacidad compartida excedida')
        peaks[e] = dict(ocupacion_maxima=p, cargas_simultaneas_maximas=c, capacidad_fisica=physical[e], conexiones=plugs[e])
    return dict(verificado=True, corridas=len(expected), buses=len(schedules), km=total_km,
                carga_kwh=total_q, sesiones=sessions, costo_buses_usd=250*len(schedules),
                costo_km_usd=.5*total_km, costo_energia_usd=total_energy_cost, costo_sesiones_usd=5*sessions,
                costo_total_usd=250*len(schedules)+.5*total_km+total_energy_cost+5*sessions,
                energia_minima_kwh=min(j['energia_minima_kwh'] for j in journeys), capacidades=peaks), journeys, activities
