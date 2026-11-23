"""Pruebas de costo_espera.py.

    python3 -m pytest -q 09-entrega3/kpi/test_costo_espera.py
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import costo_espera as ce  # noqa: E402


def _a(bus, tipo, ini, fin):
    return dict(bus_id=bus, tipo=tipo, inicio_s=str(ini), fin_s=str(fin))


def test_cuenta_solo_la_espera_entre_la_primera_salida_y_la_ultima_llegada():
    actividades = [
        _a('B1', 'espera', -600, 0),        # antes de salir: no cuenta
        _a('B1', 'servicio', 0, 600),
        _a('B1', 'espera', 600, 1200),      # entre corridas: 10 min
        _a('B1', 'carga', 1200, 1500),      # cargando: no es espera
        _a('B1', 'servicio', 1500, 2100),
        _a('B1', 'espera', 2100, 9000),     # después de terminar: no cuenta
    ]
    assert ce.minutos_de_espera(actividades) == pytest.approx(10)


def test_suma_varios_buses_y_ignora_buses_sin_servicio():
    actividades = [
        _a('B1', 'servicio', 0, 60), _a('B1', 'espera', 60, 180), _a('B1', 'servicio', 180, 240),
        _a('B2', 'servicio', 0, 60), _a('B2', 'espera', 60, 120), _a('B2', 'servicio', 120, 180),
        _a('B3', 'espera', 0, 6000),
    ]
    assert ce.minutos_de_espera(actividades) == pytest.approx(3)


def test_lee_el_precio_del_enunciado():
    assert ce.precio_espera() == pytest.approx(0.03)
