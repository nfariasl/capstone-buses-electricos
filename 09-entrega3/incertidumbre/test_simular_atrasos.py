"""Pruebas de simular_atrasos.py.

    python3 -m pytest -q 09-entrega3/incertidumbre/test_simular_atrasos.py
"""
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import simular_atrasos as sa  # noqa: E402


def _a(orden, tipo, ini, fin, e0, e1, carga=0.0):
    return dict(bus_id='B1', orden=str(orden), tipo=tipo, inicio_s=str(ini), fin_s=str(fin),
                carga_kwh=str(carga), energia_inicial_kwh=str(e0), energia_final_kwh=str(e1))


PLAN = [
    _a(1, 'servicio', 0, 1000, 350, 300),
    _a(2, 'espera', 1000, 1200, 300, 300),
    _a(3, 'servicio', 1200, 2200, 300, 250),
    _a(4, 'carga', 2200, 2800, 250, 310, carga=60),
    _a(5, 'servicio', 3000, 4000, 310, 260),
]


class FactorFijo:
    """Generador falso: todos los factores lognormales valen lo mismo."""
    def __init__(self, valor):
        self.valor = valor

    def lognormal(self, _mu, _sigma, n):
        return np.full(n, self.valor)


def test_sin_variabilidad_no_hay_atrasos_ni_energia_perdida():
    buses = sa.leer_buses(PLAN)
    atrasos, minimos = sa.simular(buses, 0.0, np.random.default_rng(1))
    assert list(atrasos) == [0, 0, 0]
    assert minimos[0] == pytest.approx(250)


def test_la_espera_absorbe_y_la_recarga_atrasada_carga_menos():
    buses = sa.leer_buses(PLAN)
    # Con factor 1,3 la primera corrida termina en 1300: la segunda sale 100 s tarde y termina en 2600;
    # la carga reservada hasta 2800 solo dura 200 de sus 600 s, así que entrega 20 de 60 kWh.
    atrasos, minimos = sa.simular(buses, 0.2, FactorFijo(1.3))
    assert list(atrasos) == pytest.approx([0, 100, 0])
    assert minimos[0] == pytest.approx(220)   # 250 + 20 - 50


def test_factores_tienen_media_uno():
    f = sa.factores(200_000, 0.2, np.random.default_rng(7))
    assert f.mean() == pytest.approx(1, abs=0.005)
    assert f.std() == pytest.approx(0.2, abs=0.005)
