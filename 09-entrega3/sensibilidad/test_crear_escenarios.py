"""Pruebas de crear_escenarios.py con un caso mediano del repositorio.

    python3 -m pytest -q 09-entrega3/sensibilidad/test_crear_escenarios.py
"""
import json
import sys
from pathlib import Path

import pytest

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ))
import crear_escenarios as ce  # noqa: E402

CASO = RAIZ / '09-entrega3/octetos/casos/mediano_400_sector_1_5_rutas'
pytestmark = pytest.mark.skipif(not CASO.exists(), reason='falta el caso del repositorio')


def _spec(carpeta):
    return json.loads((carpeta / 'escenario.json').read_text(encoding='utf-8'))


def test_crea_todos_los_escenarios(tmp_path):
    filas = ce.crear(CASO, tmp_path)
    assert [f['escenario'] for f in filas] == list(ce.ESCENARIOS)
    base = json.loads((CASO / 'escenario.json').read_text(encoding='utf-8-sig'))
    menos = _spec(tmp_path / 'plazas_-20')
    assert menos['capacidad_fisica']['E2'] == 144 and menos['conexiones']['E2'] == 144
    assert _spec(tmp_path / 'conexiones_-50')['capacidad_fisica'] == base['capacidad_fisica']
    assert _spec(tmp_path / 'cierre_E3')['capacidad_fisica']['E3'] == 0
    punta = [p for _, _, p in _spec(tmp_path / 'tarifa_punta_+50')['tarifas']]
    assert max(punta) == pytest.approx(0.33) and min(punta) == pytest.approx(0.1)
    for f in ('corridas.csv', 'distancias.csv'):
        assert (tmp_path / 'plazas_+50' / f).read_bytes() == (CASO / f).read_bytes()


def test_redistribuir_conserva_el_total(tmp_path):
    ce.crear(CASO, tmp_path, ['plazas_por_demanda'])
    s = _spec(tmp_path / 'plazas_por_demanda')
    assert sum(s['capacidad_fisica'].values()) == 700
    assert s['capacidad_fisica']['E1'] == 700  # el caso solo tiene corridas del sector 1


def test_los_escenarios_cargan_y_se_resuelven(tmp_path):
    from metodo_hibrido.caso_base import load_instance, solve
    from metodo_hibrido.verificar import verificar
    ce.crear(CASO, tmp_path, ['cierre_E1', 'plazas_-20'])
    for nombre in ('cierre_E1', 'plazas_-20'):
        trips, *params = load_instance(tmp_path / nombre)
        reporte = verificar(solve(trips, *params)[-1], trips, *params)[0]
        assert reporte['verificado']
    assert reporte['capacidades']['E1']['capacidad_fisica'] == 120


def test_no_pisa_escenarios_existentes(tmp_path):
    ce.crear(CASO, tmp_path, ['plazas_+20'])
    with pytest.raises(FileExistsError):
        ce.crear(CASO, tmp_path, ['plazas_+20'])


def test_escenarios_fisicos_declaran_parametros_y_entorno(tmp_path):
    ce.crear(CASO, tmp_path, ['bateria_250', 'consumo_+20'])
    bateria = _spec(tmp_path / 'bateria_250')
    assert bateria['parametros']['bateria_kwh'] == 250 and bateria['parametros']['reserva_kwh'] == 25
    assert bateria['sensibilidad']['entorno'] == {'BATERIA_KWH': '250', 'RESERVA_KWH': '25'}
    consumo = _spec(tmp_path / 'consumo_+20')
    assert consumo['parametros']['consumo_kwh_km'] == pytest.approx(1.68)
    assert consumo['sensibilidad']['entorno'] == {'CONSUMO_KWH_KM': '1.68'}
    assert consumo['capacidad_fisica'] == json.loads((CASO / 'escenario.json').read_text(encoding='utf-8-sig'))['capacidad_fisica']
