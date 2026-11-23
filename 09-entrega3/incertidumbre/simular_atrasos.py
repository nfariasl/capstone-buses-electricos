"""Incertidumbre: qué le pasa a un plan cuando los tiempos de viaje no son los programados.

Los planes suponen tiempos de viaje fijos (GTFS para las corridas, 18 km/h para los traslados en
vacío). Aquí se toma un plan ya auditado y se simula su día con tiempos aleatorios:

- Cada corrida y cada traslado en vacío dura su tiempo programado × F, con F lognormal de media 1 y
  coeficiente de variación CV (10, 20 y 30 %). Los F son independientes.
- Un bus nunca sale antes de la hora programada de su siguiente actividad; si llega tarde, sale tarde
  y el atraso se arrastra. La espera programada absorbe atrasos.
- Recarga: el cargador está reservado hasta la hora programada de término (lo usa otro bus después).
  Si el bus llega tarde, carga solo lo que alcanza hasta esa hora (energía proporcional al tiempo) y
  si llega después del término, no carga. La energía de cada corrida y traslado no cambia (depende de
  los km, no del tiempo).
- No hay despachadores, buses de reserva ni reprogramación: es el plan tal como se publicó.

Indicadores por réplica: % de corridas que salen con más de 5 min de atraso, atraso medio de salida,
percentil 95 y máximo, y buses cuya batería baja de la reserva (o de cero) por recargas incompletas.

Uso, desde la raíz del repositorio:
    python3 09-entrega3/incertidumbre/simular_atrasos.py [--replicas 20]
"""
import argparse
import csv
import math
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ / '09-entrega3/kpi'))
from planes import PLANES  # noqa: E402

CVS = (0.10, 0.20, 0.30)
UMBRAL_ATRASO_S = 300
RESERVA_KWH = 35.0
SALIDA = AQUI / 'resultados'


def leer_buses(actividades):
    """Actividades agrupadas por bus y ordenadas: (tipo, inicio, fin, delta_kwh), con la energía inicial del bus."""
    por_bus = defaultdict(list)
    for a in actividades:
        por_bus[a['bus_id']].append(a)
    buses = []
    for filas in por_bus.values():
        filas.sort(key=lambda a: int(a['orden']))
        pasos = []
        for a in filas:
            ini, fin = float(a['inicio_s']), float(a['fin_s'])
            if a['tipo'] == 'carga':
                delta = float(a['carga_kwh'])
            else:
                delta = float(a['energia_final_kwh']) - float(a['energia_inicial_kwh'])
            pasos.append((a['tipo'], ini, fin, delta))
        buses.append((float(filas[0]['energia_inicial_kwh']), pasos))
    return buses


def factores(n, cv, rng):
    """n factores lognormales de media 1 y coeficiente de variación cv."""
    if cv == 0:
        return np.ones(n)
    sigma = math.sqrt(math.log(1 + cv * cv))
    return rng.lognormal(-sigma * sigma / 2, sigma, n)


def simular(buses, cv, rng):
    """Una réplica. Devuelve los atrasos de salida de cada corrida (s) y la energía mínima de cada bus."""
    n_mov = sum(1 for _, pasos in buses for p in pasos if p[0] in ('servicio', 'vacio'))
    f = iter(factores(n_mov, cv, rng))
    atrasos, minimos = [], []
    for energia, pasos in buses:
        t, minimo = -math.inf, energia
        for tipo, ini, fin, delta in pasos:
            if tipo in ('servicio', 'vacio'):
                salida = max(t, ini)
                if tipo == 'servicio':
                    atrasos.append(salida - ini)
                t = salida + (fin - ini) * next(f)
                energia += delta
            elif tipo == 'carga':
                if t <= ini:
                    energia += delta
                    t = fin
                elif t < fin:
                    energia += delta * (fin - t) / (fin - ini)
                    t = fin
                # si llega después del término, no carga y sigue con su atraso
            minimo = min(minimo, energia)
        minimos.append(minimo)
    return np.array(atrasos), np.array(minimos)


def indicadores(atrasos, minimos, reserva=RESERVA_KWH):
    return dict(pct_atrasadas_5min=100 * float(np.mean(atrasos > UMBRAL_ATRASO_S)),
                atraso_medio_min=float(np.mean(atrasos)) / 60,
                atraso_p95_min=float(np.percentile(atrasos, 95)) / 60,
                atraso_max_min=float(np.max(atrasos)) / 60,
                buses_bajo_reserva=int(np.sum(minimos < reserva - 1e-6)),
                buses_sin_energia=int(np.sum(minimos < 0)))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--replicas', type=int, default=20)
    parser.add_argument('--semilla', type=int, default=2026)
    parser.add_argument('--dias', nargs='*', default=['L'])
    args = parser.parse_args()
    SALIDA.mkdir(exist_ok=True)
    filas = []
    for nombre, dia, carpeta in PLANES:
        if dia not in args.dias:
            continue
        with (RAIZ / carpeta / 'actividades.csv').open(encoding='utf-8-sig') as f:
            buses = leer_buses(csv.DictReader(f))
        for cv in CVS:
            rng = np.random.default_rng([args.semilla, int(round(cv * 100))])   # misma semilla para ambos planes
            reps = [indicadores(*simular(buses, cv, rng)) for _ in range(args.replicas)]
            fila = dict(plan=nombre, dia=dia, cv_pct=int(round(cv * 100)), replicas=args.replicas, buses=len(buses))
            for k in reps[0]:
                valores = [r[k] for r in reps]
                fila[k] = round(float(np.mean(valores)), 3)
                fila[k + '_min'] = round(float(np.min(valores)), 3)
                fila[k + '_max'] = round(float(np.max(valores)), 3)
            filas.append(fila)
            print({k: fila[k] for k in ('plan', 'dia', 'cv_pct', 'pct_atrasadas_5min', 'atraso_medio_min',
                                        'atraso_p95_min', 'buses_bajo_reserva')}, flush=True)
    with (SALIDA / 'atrasos.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)


if __name__ == '__main__':
    main()
