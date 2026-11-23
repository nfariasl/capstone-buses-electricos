"""Lectura común de planes ya resueltos (caso base o método) para calcular KPI.

Un plan es una carpeta con tres archivos que generan `codigo/tres_fases/caso_base.py` y
`metodo_hibrido/ejecutar.py` / `buscar_mejor.py`:
  - resumen.json: totales verificados (en el caso base vienen bajo la clave «caso_base»);
  - jornadas.csv: una fila por bus;
  - recargas.csv: una fila por bloque de carga de 5 min.

Este módulo no recalcula factibilidad: lee lo que ya pasó el auditor y comprueba que los tres
archivos cuadren entre sí antes de usarlos.
"""
import json
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]

# Planes de la red completa (417 rutas).
# «metodo» es el plan final de la Entrega 3: cuartetos al azar, semilla 1, 40 min (2.400 s); en el día
# laboral da 7.351 buses. Antes eran los planes de octubre (7.427 buses en L), en
# metodo_hibrido/resultados/completa_417_{,S_,D_}2026xxxx/04_final. El nombre «metodo» no se cambia:
# kpi_planes.tabla_ahorro y uso_electroterminales comparan metodo_{día} contra caso_base_{día}.
# Las carpetas de cuartetos no están en GitHub (son pesadas); solo existen en el Mac donde se corrieron.
_CUARTETOS = '09-entrega3/octetos/resultados/planes_417_{dia}/instancia_417{sufijo}_cuartetos_azar_s1_2400s'
PLANES = [
    ('caso_base', 'L', 'codigo/output/tres_fases/red_417_L_caso_base'),
    ('caso_base', 'S', 'codigo/output/tres_fases/red_417_S_caso_base'),
    ('caso_base', 'D', 'codigo/output/tres_fases/red_417_D_caso_base'),
    ('metodo', 'L', _CUARTETOS.format(dia='L', sufijo='')),
    ('metodo', 'S', _CUARTETOS.format(dia='S', sufijo='_S')),
    ('metodo', 'D', _CUARTETOS.format(dia='D', sufijo='_D')),
]

DIAS = {'L': 'laboral', 'S': 'sábado', 'D': 'domingo'}

# Electroterminal k = sector k = depot_id k en codigo/charger_capacity.csv.
NOMBRES_E = {'E1': 'Vespucio Norte', 'E2': 'El Conquistador', 'E3': 'Los Espinos',
             'E4': 'La Reina', 'E5': 'Santa Rosa'}

BLOQUE_S = 300


@dataclass
class Plan:
    nombre: str
    dia: str
    carpeta: Path
    resumen: dict
    jornadas: pd.DataFrame
    recargas: pd.DataFrame

    @property
    def etiqueta(self):
        return f'{self.nombre}_{self.dia}'


def leer_parametros(raiz=RAIZ):
    """Parámetros del caso: consumo, batería, potencia, capacidades y tarifas."""
    par = pd.read_csv(raiz / 'codigo/parameters.csv').set_index('parameter')['value']
    bateria = float(par['battery_kwh'])
    cap = pd.read_csv(raiz / 'codigo/charger_capacity.csv')
    capacidades = {f'E{int(r.depot_id)}': dict(plazas=int(r.capacity), conexiones=int(r.max_simultaneous_charging))
                   for r in cap.itertuples()}
    tarifas = pd.read_csv(raiz / 'codigo/electricity_prices.csv')
    return dict(
        bateria_kwh=bateria,
        reserva_kwh=bateria * float(par['min_soc']),
        consumo_kwh_km=bateria / float(par['range_km']),
        potencia_kw=float(par['charge_power_kw']),
        capacidades=capacidades,
        tarifas=[(float(r.start_hour), float(r.end_hour), float(r.price_usd_kwh)) for r in tarifas.itertuples()],
    )


def leer_plan(nombre, dia, carpeta, raiz=RAIZ, validar=True):
    carpeta = Path(carpeta)
    if not carpeta.is_absolute():
        carpeta = raiz / carpeta
    resumen = json.loads((carpeta / 'resumen.json').read_text(encoding='utf-8'))
    resumen = resumen.get('caso_base', resumen)
    jornadas = pd.read_csv(carpeta / 'jornadas.csv', encoding='utf-8-sig')
    recargas = pd.read_csv(carpeta / 'recargas.csv', encoding='utf-8-sig')
    plan = Plan(nombre, dia, carpeta, resumen, jornadas, recargas)
    if validar:
        validar_plan(plan)
    return plan


def leer_planes(planes=PLANES, raiz=RAIZ):
    return [leer_plan(n, d, c, raiz) for n, d, c in planes]


def _cerca(a, b, tol=1e-6):
    return math.isclose(a, b, rel_tol=tol, abs_tol=1e-6)


def validar_plan(plan):
    """Falla si jornadas, recargas y resumen no describen el mismo plan."""
    j, r, s = plan.jornadas, plan.recargas, plan.resumen
    errores = []
    if len(j) != s['buses']:
        errores.append(f'buses: {len(j)} filas en jornadas contra {s["buses"]} en resumen')
    if j['bus_id'].duplicated().any():
        errores.append('bus_id repetido en jornadas')
    if int(j['corridas'].sum()) != s['corridas']:
        errores.append(f'corridas: {j["corridas"].sum()} contra {s["corridas"]}')
    if not _cerca(j['km_servicio'].sum() + j['km_vacio'].sum(), s['km']):
        errores.append('km de jornadas no cuadra con resumen')
    if not _cerca(j['carga_kwh'].sum(), s['carga_kwh']) or not _cerca(r['carga_kwh'].sum(), s['carga_kwh']):
        errores.append('energía cargada no cuadra entre jornadas, recargas y resumen')
    if int(j['sesiones'].sum()) != s['sesiones']:
        errores.append('sesiones no cuadran con resumen')
    if not _cerca(j['costo_usd'].sum(), s['costo_total_usd']):
        errores.append('costo de jornadas no cuadra con resumen')
    if not set(r['bus_id']) <= set(j['bus_id']):
        errores.append('recargas de buses que no están en jornadas')
    if (r['tipo'] != 'carga').any():
        errores.append('recargas.csv trae filas que no son de carga')
    if (r['origen'] != r['destino']).any():
        errores.append('una carga con origen distinto de destino')
    if errores:
        raise ValueError(f'Plan {plan.etiqueta} inconsistente: ' + '; '.join(errores))


def bloques(recargas, bloque_s=BLOQUE_S):
    """Expande cada fila de recarga a los bloques de 5 min que ocupa, repartiendo su energía."""
    filas = []
    for fila in recargas.itertuples(index=False):
        ini, fin = float(fila.inicio_s), float(fila.fin_s)
        if fin <= ini:
            continue
        b = math.floor(ini / bloque_s)
        while b * bloque_s < fin:
            a, z = max(ini, b * bloque_s), min(fin, (b + 1) * bloque_s)
            if z > a:
                filas.append((fila.origen, b * bloque_s, fila.bus_id, fila.carga_kwh * (z - a) / (fin - ini)))
            b += 1
    return pd.DataFrame(filas, columns=['electroterminal', 'bloque_s', 'bus_id', 'carga_kwh'])


def tarifa(segundo, tarifas):
    """Precio USD/kWh del instante, con la hora reducida a 0-24 (el horizonte pasa de las 24:00)."""
    h = (segundo / 3600) % 24
    for ini, fin, precio in tarifas:
        if ini <= h < fin:
            return precio
    raise ValueError(f'Hora sin tarifa: {h}')
