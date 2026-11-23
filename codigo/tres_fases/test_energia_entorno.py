"""La batería, la reserva y el consumo del caso base se pueden cambiar por entorno (sensibilidad)."""
import os
import subprocess
import sys
import unittest
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
LEER = 'from tres_fases import fase3, verificar; print(fase3.BATERIA, fase3.MINIMO, fase3.CONSUMO, verificar.BATERIA)'


def constantes(**entorno):
    env = {k: v for k, v in os.environ.items() if k not in ('BATERIA_KWH', 'RESERVA_KWH', 'CONSUMO_KWH_KM')}
    return subprocess.run([sys.executable, '-c', LEER], cwd=BASE, env={**env, **entorno},
                          capture_output=True, text=True)


class EnergiaPorEntorno(unittest.TestCase):
    def test_sin_entorno_usa_el_enunciado(self):
        self.assertEqual(constantes().stdout.split(), ['350.0', '35.0', '1.4', '350.0'])

    def test_el_entorno_cambia_bateria_reserva_y_consumo(self):
        salida = constantes(BATERIA_KWH='250', RESERVA_KWH='25', CONSUMO_KWH_KM='1.68').stdout.split()
        self.assertEqual(salida, ['250.0', '25.0', '1.68', '250.0'])

    def test_rechaza_reserva_mayor_que_la_bateria(self):
        resultado = constantes(BATERIA_KWH='30', RESERVA_KWH='35')
        self.assertNotEqual(resultado.returncode, 0)
        self.assertIn('reserva', resultado.stderr)


if __name__ == '__main__':
    unittest.main()
