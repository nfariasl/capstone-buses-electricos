"""La respuesta perfecta pasa el revisor, cuesta lo que dice el modelo y no la supera ninguna heurística."""
import copy
import unittest
from metodo_hibrido.caso_base import solve
from metodo_hibrido.exacto import _podar, resolver_exacto
from metodo_hibrido.grupos import buscar_grupos
from metodo_hibrido.intercambios import buscar
from metodo_hibrido.test_caso_base import instance
from metodo_hibrido.test_grupos import OPCIONES, escenario
from metodo_hibrido.trios import buscar_trios
from metodo_hibrido.verificar import verificar


class RespuestaPerfecta(unittest.TestCase):
    def comprobar(self, trips, params, podar=False):
        plans, info = resolver_exacto(trips, *params, limit=60, podar=podar)
        self.assertTrue(info['optimo'], info)
        reporte = verificar(plans, trips, *params)[0]
        self.assertAlmostEqual(reporte['costo_total_usd'], info['objetivo_usd'], places=4)
        return plans, reporte

    def test_ninguna_heuristica_es_mas_barata(self):
        trips, params, plans = escenario()
        lookup = {t['corrida_id']: t for t in trips}
        _, perfecta = self.comprobar(trips, params)
        busquedas = [lambda p: buscar(p, lookup, *params, **OPCIONES),
                     lambda p: buscar_trios(p, lookup, *params, **OPCIONES),
                     lambda p: buscar_grupos(p, lookup, *params, k=4, **OPCIONES)]
        for busqueda in busquedas:
            resultado = busqueda(copy.deepcopy(plans))[0]
            costo = verificar(resultado, trips, *params)[0]['costo_total_usd']
            self.assertLessEqual(perfecta['costo_total_usd'], costo + 1e-6)

    def test_recarga_cuando_evita_un_bus(self):
        trips, *params = instance()
        _, perfecta = self.comprobar(trips, params)
        construido = solve(trips, *params)[0]
        self.assertEqual(perfecta['buses'], 1)
        self.assertEqual(perfecta['sesiones'], 1)
        # El margen numérico de la batería (MARGEN_KWH) encarece la carga en fracciones de centavo.
        self.assertLessEqual(perfecta['costo_total_usd'], construido['costo_total_usd'] + 1e-3)

    def test_sin_tiempo_para_recargar_usa_dos_buses(self):
        trips, *params = instance(gap=0)
        _, perfecta = self.comprobar(trips, params)
        self.assertEqual(perfecta['buses'], 2)
        self.assertEqual(perfecta['sesiones'], 0)


    def test_podar_da_el_mismo_optimo(self):
        for trips, params in [(lambda t, *p: (t, p))(*instance()), (lambda t, *p: (t, p))(*instance(gap=0)),
                              escenario()[:2]]:
            _, completa = self.comprobar(trips, params)
            _, podada = self.comprobar(trips, params, podar=True)
            self.assertAlmostEqual(completa['costo_total_usd'], podada['costo_total_usd'], places=4)


class Poda(unittest.TestCase):
    def opcion(self, e, km1, km2, maxq, price):
        return dict(e=e, km1=km1, km2=km2, maxq=maxq, price=price, start=0, end=300)

    def test_quita_solo_las_dominadas(self):
        a = self.opcion('E1', 1, 1, 30, .1)
        mas_cara = self.opcion('E1', 1, 1, 30, .2)
        carga_menos = self.opcion('E2', 2, 1, 15, .1)
        mas_lejos_pero_carga_mas = self.opcion('E3', 2, 2, 45, .1)
        mas_cerca_pero_mas_cara = self.opcion('E4', .5, .5, 30, .3)
        quedan = _podar([a, mas_cara, carga_menos, mas_lejos_pero_carga_mas, mas_cerca_pero_mas_cara])
        self.assertCountEqual([c['e'] for c in quedan], ['E1', 'E3', 'E4'])
        self.assertEqual(next(c for c in quedan if c['e'] == 'E1')['price'], .1)


if __name__ == '__main__':
    unittest.main()
