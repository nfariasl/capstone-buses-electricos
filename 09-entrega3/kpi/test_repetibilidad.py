import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import repetibilidad as rep  # noqa: E402

PAR = dict(bateria_kwh=350.0, potencia_kw=180.0,
           capacidades={'E1': dict(plazas=2, conexiones=2), 'E2': dict(plazas=1, conexiones=1)})


def _actividades():
    # B1: sale a las 06:00 y llega a las 22:00 (ventana de 8 h); B2: sale a las 05:00 y llega a la 01:00 (+1).
    filas = [
        ('B1', 'espera', 'T1', 'T1', -7200, 21600), ('B1', 'servicio', 'T1', 'T2', 21600, 79200),
        ('B1', 'espera', 'T2', 'T2', 79200, 99000),
        ('B2', 'espera', 'T1', 'T1', -7200, 18000), ('B2', 'vacio', 'T1', 'T3', 18000, 20000),
        ('B2', 'servicio', 'T3', 'E2', 20000, 90000), ('B2', 'espera', 'E2', 'E2', 90000, 99000),
    ]
    return pd.DataFrame(filas, columns=['bus_id', 'tipo', 'origen', 'destino', 'inicio_s', 'fin_s'])


def test_ventana_nocturna_ignora_las_esperas_de_relleno():
    v = rep.ventanas(_actividades()).set_index('bus_id')
    assert v.at['B1', 'ventana_h'] == 8.0
    assert v.at['B2', 'ventana_h'] == 4.0


def test_tabla_por_electroterminal():
    jornadas = pd.DataFrame(dict(bus_id=['B1', 'B2'], sector_id=[1, 2], terminal_final=['T2', 'E2'],
                                 energia_final_kwh=[170.0, 50.0]))
    t = rep.tabla(jornadas, rep.ventanas(_actividades()), PAR, 'metodo_L').set_index('electroterminal')
    e1 = t.loc['E1']
    assert math.isclose(e1['energia_a_reponer_mwh'], 0.18)
    assert math.isclose(e1['mw_instalados'], 0.36)
    assert math.isclose(e1['horas_con_todas_las_conexiones'], 0.5)
    assert e1['conexiones_necesarias'] == 1 and e1['conexiones_faltantes'] == 0
    e2 = t.loc['E2']
    assert math.isclose(e2['energia_a_reponer_mwh'], 0.30)
    assert math.isclose(e2['energia_entregable_mwh'], 0.72)
    assert e2['buses_terminan_en_e'] == 1
    total = t.loc['Total']
    assert math.isclose(total['energia_a_reponer_mwh'], 0.48)
    assert total['buses_sector'] == 2


def test_faltan_conexiones_si_la_ventana_no_alcanza():
    jornadas = pd.DataFrame(dict(bus_id=['B1', 'B2'], sector_id=[1, 1], terminal_final=['T2', 'T1'],
                                 energia_final_kwh=[0.0, 0.0]))
    par = dict(PAR, capacidades={'E1': dict(plazas=1, conexiones=1), 'E2': dict(plazas=1, conexiones=1)})
    t = rep.tabla(jornadas, rep.ventanas(_actividades()), par, 'x').set_index('electroterminal')
    # 700 kWh con 1 conexión de 180 kW en la ventana mediana de 6 h (1,08 MWh): alcanza con 1.
    assert t.at['E1', 'conexiones_necesarias'] == 1
    par_lenta = dict(par, potencia_kw=50.0)
    t = rep.tabla(jornadas, rep.ventanas(_actividades()), par_lenta, 'x').set_index('electroterminal')
    # 700 kWh a 50 kW en 6 h: 0,7 / 0,3 = 2,33, o sea 3 conexiones; faltan 2.
    assert t.at['E1', 'conexiones_necesarias'] == 3 and t.at['E1', 'conexiones_faltantes'] == 2
