"""El programa de corridas escribe una fila auditada por corrida, retoma lo hecho y no pisa tablas."""
import tempfile
import unittest
from pathlib import Path

from correr_metodos import correr
from crear_casos import crear_casos
from metodo_hibrido.caso_base import read_csv

NOMBRE_CASO = 'muy_chico_03_ruta_I10N'
METODOS = ['solo_base', 'pares', 'cuartetos']
CASO = None


def setUpModule():
    # Los casos muy chicos ya no se guardan en el repositorio: se recrean desde la instancia de 212 rutas.
    global CASO, _CARPETA
    _CARPETA = tempfile.TemporaryDirectory()
    crear_casos(Path(_CARPETA.name) / 'casos')
    CASO = Path(_CARPETA.name) / 'casos' / NOMBRE_CASO


def tearDownModule():
    _CARPETA.cleanup()


class Corridas(unittest.TestCase):
    def test_una_fila_por_corrida_y_ninguna_peor_que_el_plan_inicial(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / 'tabla.csv'
            correr([CASO], METODOS, [5], selecciones=['parecidos', 'azar'], semillas=[1], salida=salida)
            filas = read_csv(salida)
            # solo_base y pares, más cuartetos con «parecidos» y con «azar» (semilla 1).
            self.assertEqual([(f['metodo'], f['seleccion']) for f in filas],
                             [('solo_base', ''), ('pares', ''), ('cuartetos', 'parecidos'), ('cuartetos', 'azar')])
            self.assertTrue(all(f['error'] == '' for f in filas))
            inicial = float(filas[0]['costo_total_usd'])
            self.assertTrue(all(float(f['costo_total_usd']) <= inicial + 1e-6 for f in filas))

    def test_continuar_salta_lo_hecho_y_no_se_pisa_una_tabla(self):
        with tempfile.TemporaryDirectory() as tmp:
            salida = Path(tmp) / 'tabla.csv'
            correr([CASO], ['solo_base'], [5], salida=salida)
            with self.assertRaises(FileExistsError):
                correr([CASO], ['solo_base'], [5], salida=salida)
            nuevas = correr([CASO], ['solo_base', 'pares'], [5], salida=salida, continuar=True)
            self.assertEqual([f['metodo'] for f in nuevas], ['pares'])
            self.assertEqual(len(read_csv(salida)), 2)

    def test_planes_guarda_una_carpeta_auditada_por_corrida_y_reescribe_una_incompleta(self):
        with tempfile.TemporaryDirectory() as tmp:
            planes = Path(tmp) / 'planes'
            # Una carpeta que quedó de una corrida interrumpida (sin fila en la tabla) se reemplaza.
            (planes / f'{CASO.name}_pares_5s').mkdir(parents=True)
            salida = Path(tmp) / 'tabla.csv'
            correr([CASO], ['solo_base', 'pares'], [5], salida=salida, planes=planes)
            self.assertTrue(all(f['error'] == '' for f in read_csv(salida)))
            for nombre in (f'{CASO.name}_solo_base_0s', f'{CASO.name}_pares_5s'):
                for archivo in ('planes.json', 'resumen.json', 'jornadas.csv'):
                    self.assertTrue((planes / nombre / archivo).exists(), f'{nombre}/{archivo}')


if __name__ == '__main__':
    unittest.main()
