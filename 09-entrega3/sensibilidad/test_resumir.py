import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location('resumir', Path(__file__).with_name('resumir.py'))
resumir = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(resumir)


def _fila(instancia, metodo, buses, costo, error=''):
    return dict(instancia=instancia, metodo=metodo, buses=str(buses), costo_total_usd=str(costo), km='1',
                carga_kwh='1', error=error)


def test_delta_contra_la_base_del_mismo_metodo():
    filas = [_fila('instancia_417', 'cuartetos', 100, 1000.0), _fila('instancia_417', 'solo_base', 110, 1100.0),
             _fila('cierre_E1', 'cuartetos', 105, 1050.0)]

    tabla = {(r['escenario'], r['metodo']): r for r in resumir.resumir(filas)}

    assert tabla[('cierre_E1', 'cuartetos')]['delta_buses'] == 5
    assert tabla[('cierre_E1', 'cuartetos')]['delta_costo_pct'] == 5.0
    assert tabla[('base', 'cuartetos')]['delta_costo_pct'] == 0.0


def test_escenario_con_error_queda_sin_delta():
    filas = [_fila('instancia_417', 'cuartetos', 100, 1000.0), _fila('cierre_E2', 'cuartetos', '', '', error='X')]

    tabla = {r['escenario']: r for r in resumir.resumir(filas)}

    assert 'delta_costo_pct' not in tabla['cierre_E2']
    assert tabla['cierre_E2']['error'] == 'X'
