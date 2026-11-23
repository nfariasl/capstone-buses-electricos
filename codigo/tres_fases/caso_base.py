"""Caso base miope: cada ruta con sus propios buses y recarga completa cuando la batería no alcanza.

Ejecutar: python tres_fases/caso_base.py --base output/tres_fases/muestra_212 [--umbral 0.3]
O sobre una instancia del híbrido (rutas, horizonte y tipo de día):
  python tres_fases/caso_base.py --instancia ../metodo_hibrido/instancia_417_S --salida output/tres_fases/red_S_caso_base
Con --umbral, además va a cargar apenas el SOC baja de esa fracción (por defecto 0: solo cuando no alcanza).
Batería, reserva y consumo se cambian con BATERIA_KWH, RESERVA_KWH y CONSUMO_KWH_KM (sensibilidad).
No optimiza: sirve de referencia intuitiva sobre la misma instancia y la misma auditoría del modelo.
"""
import sys
from pathlib import Path
BASE = Path(__file__).resolve().parents[1]
if sys.platform == 'win32':  # .deps trae binarios de Windows; en otros sistemas se usa el entorno local
    sys.path.insert(0, str(BASE/'.deps'))
sys.path.insert(0, str(BASE))
import argparse
import json
import math
import time
from collections import defaultdict
from tres_fases.datos import CONFIG, cargar, corridas, guardar, leer
from tres_fases.fase3 import (BATERIA, BLOQUE, CONSUMO, EPS, MAX_CARGA, MINIMO, Calendario,
                              actividad, agregar_viaje, esperar)
from tres_fases.verificar import verificar

UMBRAL = 0.

def reservas(trips, distances, starts, physical):
    """Energía para llegar desde el final de cada corrida al E y al T más cercanos."""
    result = {}
    for t in trips:
        stop = 'S:'+t['fin_stop_id']
        if stop in result:
            continue
        to_e = min(distances[stop, e][0] for e in physical if (stop, e) in distances)
        to_t = min(distances[stop, s][0] for s in starts if (stop, s) in distances)
        result[stop] = CONSUMO*max(to_e, to_t)
    return result

def plan_recarga(bus, target, latest, distances, calendar):
    """E más cercano con cupo para cargar al 100 % antes de `latest`; si no cabe, prueba el siguiente."""
    origin = bus['loc']
    reachable = [e for e in calendar.physical if (origin, e) in distances and (e, target) in distances]
    for e in sorted(reachable, key=lambda e: (distances[origin, e][0], e)):
        km1, dt1 = distances[origin, e]
        km2, dt2 = distances[e, target]
        arrival_soc = bus['soc']-CONSUMO*km1
        if arrival_soc < MINIMO-EPS:
            continue
        q = BATERIA-arrival_soc
        blocks = max(1, math.ceil(q/MAX_CARGA-EPS))
        start = math.ceil((bus['libre']+dt1)/BLOQUE)*BLOQUE
        while start+blocks*BLOQUE+dt2 <= latest:
            if calendar.libre(e, start, start+blocks*BLOQUE, True):
                return dict(e=e, start=start, end=start+blocks*BLOQUE, q=q, km2=km2, dt1=dt1)
            start += BLOQUE
    return None

def evaluar(bus, trip, distances, calendar, umbral, reserve):
    """Plan para que `bus` cubra `trip`, o None. Recarga si bajó del umbral o si no le alcanza."""
    target, endstop = 'S:'+trip['inicio_stop_id'], 'S:'+trip['fin_stop_id']
    if (bus['loc'], target) not in distances:
        return None
    km, dt = distances[bus['loc'], target]
    need = CONSUMO*trip['distancia_servicio_km']+reserve[endstop]
    on_time = bus['libre']+dt <= trip['inicio_s']
    enough = bus['soc']-CONSUMO*km-need >= MINIMO-EPS
    if bus['soc'] >= umbral*BATERIA-EPS and on_time and enough:
        return dict(carga=None)
    charge = plan_recarga(bus, target, trip['inicio_s'], distances, calendar)
    if charge and BATERIA-CONSUMO*charge['km2']-need >= MINIMO-EPS:
        return dict(carga=charge)
    return None

def aplicar(bus, trip, plan, distances, calendar):
    acts = bus['actividades']
    target, endstop = 'S:'+trip['inicio_stop_id'], 'S:'+trip['fin_stop_id']
    c = plan['carga']
    if c:
        esperar(acts, bus['loc'], bus['libre'], c['start']-c['dt1'])
        agregar_viaje(acts, bus['loc'], c['e'], c['start']-c['dt1'], distances)
        for n, s in enumerate(range(c['start'], c['end'], BLOQUE)):
            acts.append(actividad('carga', c['e'], c['e'], s, s+BLOQUE, q=min(MAX_CARGA, c['q']-n*MAX_CARGA)))
        calendar.reservar(c['e'], c['start'], c['end'], True)
        arrival = agregar_viaje(acts, c['e'], target, c['end'], distances)
        soc = BATERIA-CONSUMO*c['km2']
    else:
        arrival = agregar_viaje(acts, bus['loc'], target, bus['libre'], distances)
        soc = bus['soc']-CONSUMO*distances[bus['loc'], target][0]
    esperar(acts, target, arrival, trip['inicio_s'])
    acts.append(actividad('servicio', target, endstop, trip['inicio_s'], trip['fin_s'],
                          trip['distancia_servicio_km'], trip=trip['corrida_id']))
    bus.update(loc=endstop, libre=trip['fin_s'], soc=soc-CONSUMO*trip['distancia_servicio_km'])
    bus['corridas'].append(trip['corrida_id'])

def bus_nuevo(trip, distances, starts, t0, number, reserve):
    """Bus con batería llena que sale del T más cercano justo a tiempo."""
    origin = 'S:'+trip['inicio_stop_id']
    candidates = [s for s in starts if (s, origin) in distances and t0+distances[s, origin][1] <= trip['inicio_s']]
    if not candidates:
        raise RuntimeError(f"Ningún T alcanza la corrida {trip['corrida_id']} dentro del horizonte")
    initial = min(candidates, key=lambda s: (distances[s, origin][0], s))
    km, dt = distances[initial, origin]
    if BATERIA-CONSUMO*(km+trip['distancia_servicio_km'])-reserve['S:'+trip['fin_stop_id']] < MINIMO-EPS:
        raise RuntimeError(f"La corrida {trip['corrida_id']} no cabe en una batería llena")
    acts = []
    esperar(acts, initial, t0, trip['inicio_s']-dt)
    agregar_viaje(acts, initial, origin, trip['inicio_s']-dt, distances)
    return dict(bus_id=f'C{number:05d}', cadena_fase2='ruta:'+trip['route_id'], sector_id=trip['sector_id'],
                terminal_inicial=initial, loc=origin, libre=trip['inicio_s'], soc=BATERIA-CONSUMO*km,
                corridas=[], actividades=acts)

def cerrar(bus, distances, starts, horizon):
    """Al terminar su última corrida, el bus vuelve al T más cercano y queda ahí hasta el cierre."""
    ends = [s for s in starts if (bus['loc'], s) in distances
            and bus['soc']-CONSUMO*distances[bus['loc'], s][0] >= MINIMO-EPS
            and bus['libre']+distances[bus['loc'], s][1] <= horizon]
    if not ends:
        raise AssertionError(f"{bus['bus_id']} no puede volver a un terminal común")
    final = min(ends, key=lambda s: (distances[bus['loc'], s][0], s))
    finish = agregar_viaje(bus['actividades'], bus['loc'], final, bus['libre'], distances)
    esperar(bus['actividades'], final, finish, horizon)
    return dict(bus_id=bus['bus_id'], cadena_fase2=bus['cadena_fase2'], sector_id=bus['sector_id'],
                terminal_inicial=bus['terminal_inicial'], terminal_final=final, corridas=bus['corridas'],
                actividades=bus['actividades'])

def construir_caso_base(trips, distances, starts, physical, plugs, tariffs, t0, horizon, umbral=UMBRAL):
    """Primer bus libre de la misma ruta que alcance a llegar; si ninguno llega, se agrega uno."""
    calendar = Calendario(physical, plugs, t0, horizon)
    reserve = reservas(trips, distances, starts, physical)
    fleets, buses = defaultdict(list), []
    for trip in sorted(trips, key=lambda t: (t['inicio_s'], t['corrida_id'])):
        fleet = fleets[trip['route_id']]
        for bus in sorted(fleet, key=lambda b: (b['libre'], b['bus_id'])):
            plan = evaluar(bus, trip, distances, calendar, umbral, reserve)
            if plan:
                aplicar(bus, trip, plan, distances, calendar)
                break
        else:
            bus = bus_nuevo(trip, distances, starts, t0, len(buses)+1, reserve)
            aplicar(bus, trip, dict(carga=None), distances, calendar)
            fleet.append(bus)
            buses.append(bus)
    return [cerrar(b, distances, starts, horizon) for b in buses]

def rutas_horizonte_servicio(base=None, instancia=None):
    """Rutas, horizonte y tipo de día de una instancia del híbrido o, si no hay, de una corrida de ejecutar.py."""
    if instancia is not None:
        spec = json.loads((Path(instancia)/'escenario.json').read_text(encoding='utf-8-sig'))
        bounds = dict(inicio_horizonte_s=spec['inicio_horizonte_s'], fin_horizonte_s=spec['fin_horizonte_s'])
        return spec['rutas'], bounds, spec['service_id']
    routes = [r['route_id'] for r in leer(Path(base)/'seleccion_rutas.csv')]
    bounds = json.loads((Path(base)/'resumen.json').read_text(encoding='utf-8'))['horizonte']
    return routes, bounds, 'L'

def ejecutar(routes, bounds, servicio, umbral, out):
    """Construye el caso base, lo pasa por el auditor y guarda jornadas, actividades, recargas y resumen."""
    start = time.perf_counter()
    t0, horizon = int(bounds['inicio_horizonte_s']), int(bounds['fin_horizonte_s'])
    trips, distances, starts, physical, plugs, tariffs = cargar(routes, corridas(servicio))
    schedules = construir_caso_base(trips, distances, starts, physical, plugs, tariffs, t0, horizon, umbral)
    summary, journeys, activities = verificar(schedules, trips, distances, starts, physical, plugs, tariffs, t0, horizon)
    km_service = sum(j['km_servicio'] for j in journeys)
    km_empty = sum(j['km_vacio'] for j in journeys)
    out.mkdir(parents=True, exist_ok=True)
    guardar(out/'jornadas.csv', journeys)
    guardar(out/'actividades.csv', activities)
    guardar(out/'recargas.csv', [a for a in activities if a['tipo'] == 'carga'])
    result = dict(politica='Cada ruta con sus propios buses; primer bus libre que alcanza; recarga al 100 % '
                           'en el E más cercano con cupo cuando no alcanza o el SOC baja del umbral',
                  umbral_soc=umbral, servicio=servicio,
                  configuracion=dict(CONFIG, bateria_kwh=BATERIA, minimo_kwh=MINIMO, consumo_kwh_km=CONSUMO), rutas=routes, horizonte=bounds,
                  km_servicio=km_service, km_vacio=km_empty, porcentaje_km_vacio=100*km_empty/(km_service+km_empty),
                  caso_base=summary, tiempo_total_s=time.perf_counter()-start)
    (out/'resumen.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE/'output/tres_fases/muestra_212',
                        help='Carpeta de una ejecución de ejecutar.py: usa sus rutas y su horizonte')
    parser.add_argument('--instancia', type=Path,
                        help='Instancia del método híbrido: usa sus rutas, su horizonte y su tipo de día')
    parser.add_argument('--umbral', type=float, default=UMBRAL, help='Fracción de batería que dispara la recarga')
    parser.add_argument('--salida', type=Path)
    args = parser.parse_args()
    if not 0 <= args.umbral < 1:
        parser.error('--umbral debe estar entre 0 y 1')
    if args.instancia and args.salida is None:
        parser.error('--instancia requiere --salida')
    routes, bounds, servicio = rutas_horizonte_servicio(base=args.base, instancia=args.instancia)
    out = args.salida or args.base.parent/(args.base.name+'_caso_base'+('' if args.umbral == UMBRAL else f'_{args.umbral:g}'))
    result = ejecutar(routes, bounds, servicio, args.umbral, out)
    print(json.dumps({k: v for k, v in result.items() if k != 'rutas'}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
