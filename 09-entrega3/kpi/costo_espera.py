"""Costo de espera de los planes (decisión D2): 0,03 USD por minuto que un bus espera entre corridas.

Ningún plan lo cobra en su costo: el método y el caso base usan espera de costo cero. Este script lo
calcula sobre los planes ya auditados (los de kpi/planes.py) y lo suma al costo informado, para ver si
cambia la comparación contra el caso base.

Qué cuenta como espera: las actividades «espera» de actividades.csv que caen entre la primera salida
y la última llegada de cada bus. No cuenta la espera antes de salir ni después de terminar (el bus
está estacionado fuera de servicio) ni el tiempo cargando. El precio sale de 01-datos/parameters.csv.

Uso, desde la raíz del repositorio:
    python3 09-entrega3/kpi/costo_espera.py
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from planes import DIAS, PLANES, RAIZ  # noqa: E402

SALIDA = AQUI / 'resultados'


def precio_espera(raiz=RAIZ):
    with (raiz / '01-datos/parameters.csv').open(encoding='utf-8-sig') as f:
        for fila in csv.reader(f):
            if fila and fila[0] == 'waiting_cost_per_min':
                return float(fila[1])
    raise ValueError('parameters.csv no trae waiting_cost_per_min')


def minutos_de_espera(actividades):
    """Minutos de espera entre la primera salida y la última llegada de cada bus.

    `actividades` es una lista de dicts con bus_id, tipo, inicio_s y fin_s (como actividades.csv).
    """
    por_bus = defaultdict(list)
    for a in actividades:
        por_bus[a['bus_id']].append((float(a['inicio_s']), float(a['fin_s']), a['tipo']))
    total = 0.0
    for filas in por_bus.values():
        servicios = [(i, f) for i, f, t in filas if t == 'servicio']
        if not servicios:
            continue
        desde, hasta = min(i for i, _ in servicios), max(f for _, f in servicios)
        total += sum(max(0.0, min(f, hasta) - max(i, desde)) for i, f, t in filas if t == 'espera')
    return total / 60


def costos_informados():
    with (AQUI / 'resultados/kpi_planes.csv').open(encoding='utf-8-sig') as f:
        fila = next(r for r in csv.DictReader(f) if r['kpi'] == 'costo_total_usd')
    return {k: float(v) for k, v in fila.items() if k not in ('kpi', 'unidad', 'descripcion')}


def main():
    precio, costos = precio_espera(), costos_informados()
    filas = []
    for nombre, dia, carpeta in PLANES:
        with (RAIZ / carpeta / 'actividades.csv').open(encoding='utf-8-sig') as f:
            minutos = minutos_de_espera(csv.DictReader(f))
        costo = costos[f'{nombre}_{dia}']
        filas.append(dict(plan=nombre, dia=dia, minutos_espera=round(minutos, 1), costo_espera_usd=round(minutos * precio, 2),
                          costo_informado_usd=round(costo, 2), costo_con_espera_usd=round(costo + minutos * precio, 2),
                          pct_espera=round(100 * minutos * precio / costo, 2)))
    for dia in DIAS:
        base, metodo = (next(f for f in filas if f['plan'] == p and f['dia'] == dia) for p in ('caso_base', 'metodo'))
        for clave, f in (('sin', 'costo_informado_usd'), ('con', 'costo_con_espera_usd')):
            metodo[f'ahorro_{clave}_espera_pct'] = round(100 * (metodo[f] / base[f] - 1), 2)
    SALIDA.mkdir(exist_ok=True)
    with (SALIDA / 'costo_espera.csv').open('w', encoding='utf-8-sig', newline='') as f:
        campos = list(filas[0]) + ['ahorro_sin_espera_pct', 'ahorro_con_espera_pct']
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)
    for f in filas:
        print(f)


if __name__ == '__main__':
    main()
