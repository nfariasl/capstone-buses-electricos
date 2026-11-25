"""¿Cuánto queda el ahorro si se paga la recarga nocturna que le falta a cada plan?

Los dos planes parten con la flota llena (lo fija el enunciado) y terminan con menos energía. Nuestro plan
carga poco de día, así que deja más energía por reponer de noche que el caso base: parte de su ahorro en
energía es diferido. Aquí se le suma a cada plan el costo de volver a llenar sus buses de noche, a la tarifa
nocturna del enunciado (0,10 USD/kWh de 0 a 8 h; 0,11 de 22 a 24 h), con o sin una sesión de 5 USD por bus.

No cuenta los km en vacío para llegar al electroterminal ni el límite de conexiones (ver repetibilidad.py):
es el costo de la energía, no la factibilidad de cargarla.

Uso, desde la raíz del repositorio:
    python3 09-entrega3/kpi/costo_recarga_nocturna.py
Lee kpi/resultados/kpi_planes.csv y escribe kpi/resultados/costo_recarga_nocturna.csv.
"""
from pathlib import Path

import pandas as pd

RESULTADOS = Path(__file__).resolve().parent / 'resultados'
DIAS = ('L', 'S', 'D')
DIAS_POR_SEMANA = {'L': 5, 'S': 1, 'D': 1}
# (nombre, USD/kWh, USD por bus): del más barato al más caro
ESCENARIOS = (('noche_0.10_sin_sesion', 0.10, 0.0), ('noche_0.10_con_sesion', 0.10, 5.0), ('noche_0.11_con_sesion', 0.11, 5.0))


def costo_con_noche(costo, energia_kwh, buses, precio_kwh, sesion_usd):
    """Costo del día más lo que cuesta volver a llenar la flota de noche."""
    if min(costo, energia_kwh, buses, precio_kwh, sesion_usd) < 0:
        raise ValueError('Costos, energía, buses y precios no pueden ser negativos')
    return costo + precio_kwh * energia_kwh + sesion_usd * buses


def ahorro_pct(base, plan, precio_kwh, sesion_usd):
    """Cambio porcentual del costo del plan contra el caso base, con la noche incluida (negativo = ahorro)."""
    cb = costo_con_noche(base['costo'], base['energia_kwh'], base['buses'], precio_kwh, sesion_usd)
    cp = costo_con_noche(plan['costo'], plan['energia_kwh'], plan['buses'], precio_kwh, sesion_usd)
    return 100 * (cp / cb - 1)


def leer_planes(ruta):
    kpi = pd.read_csv(ruta).set_index('kpi')
    faltan = {'costo_total_usd', 'buses', 'energia_a_reponer_kwh'} - set(kpi.index)
    if faltan:
        raise SystemExit(f'Faltan filas en {ruta}: {sorted(faltan)}')
    columnas = [c for c in kpi.columns if c.startswith(('caso_base_', 'metodo_'))]
    return {col: dict(costo=float(kpi.at['costo_total_usd', col]), buses=float(kpi.at['buses', col]),
                      energia_kwh=float(kpi.at['energia_a_reponer_kwh', col])) for col in columnas}


def fila_ahorro(dia, base, plan):
    fila = dict(dia=dia, energia_base_mwh=base['energia_kwh'] / 1000, energia_plan_mwh=plan['energia_kwh'] / 1000,
                ahorro_sin_noche_pct=ahorro_pct(base, plan, 0, 0))
    fila.update({f'ahorro_{nombre}_pct': ahorro_pct(base, plan, p, s) for nombre, p, s in ESCENARIOS})
    return fila


def semana(planes, clave):
    """Una semana tipo: cinco días laborales, un sábado y un domingo."""
    return {k: sum(DIAS_POR_SEMANA[d] * planes[f'{clave}_{d}'][k] for d in DIAS) for k in ('costo', 'buses', 'energia_kwh')}


def tabla(planes):
    filas = [fila_ahorro(d, planes[f'caso_base_{d}'], planes[f'metodo_{d}']) for d in DIAS]
    filas.append(fila_ahorro('semana', semana(planes, 'caso_base'), semana(planes, 'metodo')))
    return pd.DataFrame(filas)


def main():
    resultado = tabla(leer_planes(RESULTADOS / 'kpi_planes.csv'))
    salida = RESULTADOS / 'costo_recarga_nocturna.csv'
    resultado.round(3).to_csv(salida, index=False)
    print(resultado.round(2).to_string(index=False))
    print(f'Escrito {salida}')


if __name__ == '__main__':
    main()
