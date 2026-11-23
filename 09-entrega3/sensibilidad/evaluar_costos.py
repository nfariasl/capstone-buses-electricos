"""Sensibilidad del ahorro al costo por bus y al costo por km, sin reoptimizar.

Toma los planes ya hechos (caso base y cuartetos al azar, kpi/resultados/kpi_planes.csv) y recalcula su
costo con otros precios: USD por bus ×0,8 y ×1,2, y USD por km ×0,8 y ×1,2. Energía y sesiones no
cambian. Responde si el ahorro contra el caso base se mantiene cuando los precios del enunciado
cambian; no dice cuál sería el mejor plan con esos precios (para eso habría que volver a optimizar).

Uso, desde la raíz del repositorio:
    python3 09-entrega3/sensibilidad/evaluar_costos.py
"""
import csv
from pathlib import Path

AQUI = Path(__file__).resolve().parent
KPI = AQUI.parent / 'kpi/resultados/kpi_planes.csv'
SALIDA = AQUI / 'resultados/costos_evaluados.csv'
COMPONENTES = ('costo_buses_usd', 'costo_km_usd', 'costo_energia_usd', 'costo_sesiones_usd')
ESCENARIOS = {
    'base': (1.0, 1.0), 'costo_bus_-20': (0.8, 1.0), 'costo_bus_+20': (1.2, 1.0),
    'costo_km_-20': (1.0, 0.8), 'costo_km_+20': (1.0, 1.2),
}


def costos(kpi_csv=KPI):
    with Path(kpi_csv).open(encoding='utf-8-sig') as f:
        filas = {r['kpi']: r for r in csv.DictReader(f) if r['kpi'] in COMPONENTES}
    planes = [k for k in filas['costo_buses_usd'] if k not in ('kpi', 'unidad', 'descripcion')]
    return {p: {c: float(filas[c][p]) for c in COMPONENTES} for p in planes}


def costo_total(comp, factor_bus, factor_km):
    return (comp['costo_buses_usd'] * factor_bus + comp['costo_km_usd'] * factor_km
            + comp['costo_energia_usd'] + comp['costo_sesiones_usd'])


def evaluar(comps):
    filas = []
    for nombre, (fb, fk) in ESCENARIOS.items():
        for dia in ('L', 'S', 'D'):
            base, metodo = costo_total(comps[f'caso_base_{dia}'], fb, fk), costo_total(comps[f'metodo_{dia}'], fb, fk)
            filas.append(dict(escenario=nombre, dia=dia, costo_caso_base_usd=round(base, 2),
                              costo_metodo_usd=round(metodo, 2), ahorro_pct=round(100 * (metodo / base - 1), 2)))
    return filas


def main():
    filas = evaluar(costos())
    SALIDA.parent.mkdir(exist_ok=True)
    with SALIDA.open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    for f in filas:
        print(f)


if __name__ == '__main__':
    main()
