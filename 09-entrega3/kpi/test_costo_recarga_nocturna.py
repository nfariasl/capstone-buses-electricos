"""Pruebas de costo_recarga_nocturna.py.

    python3 -m pytest -q 09-entrega3/kpi/test_costo_recarga_nocturna.py
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import costo_recarga_nocturna as crn  # noqa: E402


def test_suma_la_energia_nocturna_y_una_sesion_por_bus():
    # 1.000 USD del día + 2.000 kWh a 0,10 + 10 buses a 5 USD
    assert crn.costo_con_noche(1000, 2000, 10, precio_kwh=0.10, sesion_usd=5) == pytest.approx(1250)


def test_sin_sesion_solo_cobra_la_energia():
    assert crn.costo_con_noche(1000, 2000, 10, precio_kwh=0.10, sesion_usd=0) == pytest.approx(1200)


def test_el_ahorro_baja_si_el_plan_deja_mas_energia_por_reponer():
    base = dict(costo=100, energia_kwh=0, buses=1)
    plan = dict(costo=80, energia_kwh=100, buses=1)
    sin_noche = crn.ahorro_pct(base, plan, precio_kwh=0, sesion_usd=0)
    con_noche = crn.ahorro_pct(base, plan, precio_kwh=0.10, sesion_usd=0)
    assert sin_noche == pytest.approx(-20)
    assert con_noche == pytest.approx(-10)


def test_rechaza_valores_negativos():
    with pytest.raises(ValueError):
        crn.costo_con_noche(1000, -1, 10, precio_kwh=0.10, sesion_usd=5)
