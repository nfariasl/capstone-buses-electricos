"""¿Se puede repetir el día? Energía a reponer de noche contra lo que cada electroterminal puede entregar.

Cada plan parte con todos los buses llenos (350 kWh) y los deja con menos al final. Para repetir el mismo
plan al día siguiente, cada bus tiene que volver a llenarse entre su última llegada y su primera salida.

Supuestos (declararlos en el informe):
  - cada bus se recarga en el electroterminal de su sector (sector k = electroterminal Ek);
  - la ventana nocturna de cada bus va de su última llegada a su primera salida del día siguiente, que es la
    misma hora de hoy (el plan se repite igual); se usa la mediana de las ventanas del sector;
  - cada conexión entrega 180 kW sin pausa y la potencia del transformador no limita (no hay dato);
  - no se cuentan los km en vacío para llegar al electroterminal: 6.651 de los 7.351 buses del plan de
    cuartetos terminan en terminales sin cargadores, así que esto subestima el costo de repetir el día.

Uso, desde la raíz del repositorio (necesita actividades.csv, que no está en GitHub):
    python3 09-entrega3/kpi/repetibilidad.py

Escribe en 09-entrega3/kpi/resultados/: repetibilidad.csv y repetibilidad.md.
"""
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planes as pl  # noqa: E402

SALIDA = Path(__file__).resolve().parent / 'resultados'
DIA_S = 86400
RELLENO = 'espera'  # las actividades parten y terminan con esperas que solo rellenan el horizonte


def ventanas(actividades):
    """Por bus: primera salida, última llegada y horas libres hasta salir de nuevo al día siguiente."""
    reales = actividades[actividades['tipo'] != RELLENO]
    g = reales.groupby('bus_id').agg(salida_s=('inicio_s', 'min'), llegada_s=('fin_s', 'max')).reset_index()
    libre_s = (g['salida_s'] + DIA_S - g['llegada_s']).clip(lower=0)
    return g.assign(ventana_h=libre_s / 3600)


def _fila(plan, e, buses, terminan, kwh, conexiones, plazas, ventana_h, ventana_p10_h, potencia_kw):
    mw_instalados = conexiones * potencia_kw / 1000
    mwh = kwh / 1000
    entregable = mw_instalados * ventana_h
    por_conexion = potencia_kw / 1000 * ventana_h
    if mwh <= 0:
        necesarias = 0
    elif por_conexion > 0:
        necesarias = math.ceil(mwh / por_conexion - 1e-9)
    else:
        raise ValueError(f'{plan} {e}: hay {mwh:.1f} MWh que reponer y ventana nocturna nula')
    return dict(
        plan=plan, electroterminal=e, nombre=pl.NOMBRES_E.get(e, ''), buses_sector=buses,
        buses_terminan_en_e=terminan, plazas=plazas, conexiones=conexiones,
        energia_a_reponer_mwh=mwh, mw_instalados=mw_instalados,
        horas_con_todas_las_conexiones=mwh / mw_instalados if mw_instalados else math.inf,
        ventana_mediana_h=ventana_h, ventana_p10_h=ventana_p10_h,
        energia_entregable_mwh=entregable,
        pct_cubierto=100 * min(1.0, entregable / mwh) if mwh else 100.0,
        mw_necesarios=mwh / ventana_h if mwh > 0 else 0.0,
        conexiones_necesarias=necesarias, conexiones_faltantes=max(0, necesarias - conexiones))


def tabla(jornadas, vent, par, plan):
    """Una fila por electroterminal (y el total) con la energía a reponer y la capacidad nocturna."""
    j = jornadas.merge(vent[['bus_id', 'ventana_h']], on='bus_id', how='left')
    j = j.assign(reponer_kwh=(par['bateria_kwh'] - j['energia_final_kwh']).clip(lower=0),
                 electroterminal='E' + j['sector_id'].astype(int).astype(str))
    filas = []
    for e, cap in sorted(par['capacidades'].items()):
        g = j[j['electroterminal'] == e]
        filas.append(_fila(plan, e, len(g), int((g['terminal_final'] == e).sum()), g['reponer_kwh'].sum(),
                           cap['conexiones'], cap['plazas'], float(g['ventana_h'].median()) if len(g) else 0.0,
                           float(g['ventana_h'].quantile(0.1)) if len(g) else 0.0, par['potencia_kw']))
    df = pd.DataFrame(filas)
    total = dict(plan=plan, electroterminal='Total', nombre='', buses_sector=int(df['buses_sector'].sum()),
                 buses_terminan_en_e=int(df['buses_terminan_en_e'].sum()), plazas=int(df['plazas'].sum()),
                 conexiones=int(df['conexiones'].sum()),
                 energia_a_reponer_mwh=df['energia_a_reponer_mwh'].sum(),
                 mw_instalados=df['mw_instalados'].sum(), mw_necesarios=df['mw_necesarios'].sum(),
                 energia_entregable_mwh=df['energia_entregable_mwh'].sum(),
                 conexiones_necesarias=int(df['conexiones_necesarias'].sum()),
                 conexiones_faltantes=int(df['conexiones_faltantes'].sum()),
                 ventana_mediana_h=float(j['ventana_h'].median()), ventana_p10_h=float(j['ventana_h'].quantile(0.1)))
    total['horas_con_todas_las_conexiones'] = total['energia_a_reponer_mwh'] / total['mw_instalados']
    total['pct_cubierto'] = 100 * df[['energia_entregable_mwh', 'energia_a_reponer_mwh']].min(axis=1).sum() \
        / total['energia_a_reponer_mwh']
    return pd.concat([df, pd.DataFrame([total])], ignore_index=True)


def main():
    par = pl.leer_parametros()
    tablas = []
    for nombre, dia, carpeta in pl.PLANES:
        plan = pl.leer_plan(nombre, dia, carpeta)
        act = pd.read_csv(plan.carpeta / 'actividades.csv', encoding='utf-8-sig',
                          usecols=['bus_id', 'tipo', 'inicio_s', 'fin_s'])
        tablas.append(tabla(plan.jornadas, ventanas(act), par, plan.etiqueta))
    df = pd.concat(tablas, ignore_index=True)
    SALIDA.mkdir(exist_ok=True)
    df.to_csv(SALIDA / 'repetibilidad.csv', index=False)
    columnas = ['plan', 'electroterminal', 'buses_sector', 'energia_a_reponer_mwh', 'mw_instalados',
                'horas_con_todas_las_conexiones', 'ventana_mediana_h', 'pct_cubierto', 'mw_necesarios',
                'conexiones', 'conexiones_necesarias', 'conexiones_faltantes']
    with pd.option_context('display.float_format', '{:,.1f}'.format, 'display.width', 250):
        texto = df[columnas].to_string(index=False)
    (SALIDA / 'repetibilidad.md').write_text(
        '# Repetibilidad del día por electroterminal\n\nGenerado por `repetibilidad.py`. No editar a mano. '
        'Supuestos en el encabezado del script.\n\n```\n' + texto + '\n```\n', encoding='utf-8')
    print(texto)


if __name__ == '__main__':
    main()
