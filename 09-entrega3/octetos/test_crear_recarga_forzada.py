"""Las copias con batería chica cambian solo la batería y no se pueden correr con la batería por omisión."""
import json
import tempfile
import unittest
from pathlib import Path

from crear_casos import crear_casos, crear_por_rutas, elegir_por_rutas
from crear_recarga_forzada import crear_variante
from metodo_hibrido.caso_base import InputError, load_instance, read_csv

RAIZ = Path(__file__).resolve().parents[2]


class RecargaForzada(unittest.TestCase):
    def test_copia_sin_cambios_salvo_la_bateria_y_se_rechaza_con_otra_bateria(self):
        with tempfile.TemporaryDirectory() as tmp:
            casos = Path(tmp) / 'casos'
            crear_casos(casos)
            origen = casos / 'muy_chico_03_ruta_I10N'
            destino = crear_variante(origen, Path(tmp) / 'bat150', 150)
            for archivo in ('corridas.csv', 'distancias.csv'):
                self.assertEqual((origen / archivo).read_bytes(), (destino / archivo).read_bytes())
            escenario = json.loads((destino / 'escenario.json').read_text(encoding='utf-8'))
            self.assertEqual(escenario['parametros']['bateria_kwh'], 150)
            with self.assertRaises(InputError):
                load_instance(destino)  # las pruebas corren con la batería por omisión (350 kWh)
            with self.assertRaises(FileExistsError):
                crear_variante(origen, destino, 150)
            with self.assertRaises(ValueError):
                crear_variante(origen, Path(tmp) / 'bat30', 30)


class PorRutas(unittest.TestCase):
    def test_escalera_anidada_con_las_rutas_mas_chicas_del_sector(self):
        corridas = read_csv(RAIZ / 'metodo_hibrido/instancia_212/corridas.csv')
        casos = elegir_por_rutas(corridas, '2', [10, 6])
        self.assertEqual([len(c['rutas']) for c in casos], [6, 10])
        self.assertEqual(casos[1]['rutas'][:6], casos[0]['rutas'])
        self.assertTrue(all(r['sector_id'] == '2' for r in corridas if r['route_id'] in casos[1]['rutas']))
        with self.assertRaises(ValueError):
            elegir_por_rutas(corridas, '2', [1000])

    def test_crea_carpetas_validas(self):
        with tempfile.TemporaryDirectory() as tmp:
            indice = crear_por_rutas([6], '2', Path(tmp))
            self.assertEqual(indice[0]['nombre'], 'rutas_06_sector_2')
            load_instance(Path(tmp) / 'rutas_06_sector_2')


if __name__ == '__main__':
    unittest.main()
