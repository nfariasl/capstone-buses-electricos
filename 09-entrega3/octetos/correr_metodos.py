"""Corre todos los métodos sobre los casos, con el mismo tiempo, y junta los resultados en una tabla.

Cada método parte del mismo plan inicial (la construcción cronológica) y cada resultado pasa por el
revisor del híbrido; lo que no pasa no se usa. Las filas se escriben a medida que terminan, así que
una corrida larga interrumpida conserva lo hecho (--continuar salta lo que ya está en la tabla).

Uso, desde la raíz del proyecto, con la licencia de Gurobi cargada:
  .venv-optimizacion/bin/python 09-entrega3/octetos/correr_metodos.py --presupuestos 60 120 \\
      --salida 09-entrega3/octetos/resultados/casos_chicos.csv
"""
import argparse
import csv
import json
import shutil
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from metodo_hibrido.caso_base import load_instance, read_csv, solve  # noqa: E402
from metodo_hibrido.creciente import buscar_creciente  # noqa: E402
from metodo_hibrido.ejecutar import etapa, export  # noqa: E402
from metodo_hibrido.exacto import resolver_exacto  # noqa: E402
from metodo_hibrido.grupos import buscar_grupos  # noqa: E402
from metodo_hibrido.intercambios import buscar  # noqa: E402
from metodo_hibrido.trios import buscar_trios  # noqa: E402
from metodo_hibrido.verificar import verificar  # noqa: E402

CASOS = Path(__file__).resolve().parent / 'casos'
# Mismos parámetros de búsqueda que el método híbrido de la Entrega 2.
BUSQUEDA = dict(local_limit=2., neighbors=8, per_pair=3, max_rounds=30, coordination='conjunta')
TAMANOS = {'trios': 3, 'cuartetos': 4, 'quintetos': 5, 'octetos': 8}
METODOS = ('solo_base', 'pares', 'pares_trios', 'trios', 'cuartetos', 'quintetos', 'octetos', 'mezcla', 'exacta',
           'exacta_podada')
EXACTAS = {'exacta', 'exacta_podada'}
CON_SELECCION = {'trios', 'cuartetos', 'quintetos', 'octetos', 'mezcla'}
CAMPOS = ['instancia', 'corridas', 'metodo', 'seleccion', 'semilla', 'presupuesto_s', 'buses', 'costo_total_usd', 'km',
          'carga_kwh', 'sesiones', 'tiempo_s', 'intentos', 'mejoras', 'motivo_fin', 'optimo', 'cota_usd', 'error']


def _etapas(metodo, seleccion, semilla, presupuesto):
    """Lista de (búsqueda, opciones) que forman el método; el presupuesto total es el mismo para todos."""
    if metodo == 'pares':
        return [(buscar, dict(budget=presupuesto))]
    if metodo == 'pares_trios':
        # Como en ejecutar.py: mitad del tiempo para pares y mitad para tríos.
        return [(buscar, dict(budget=presupuesto / 2)), (buscar_trios, dict(budget=presupuesto / 2))]
    if metodo in TAMANOS:
        return [(buscar_grupos, dict(budget=presupuesto, k=TAMANOS[metodo], seleccion=seleccion, semilla=semilla))]
    if metodo == 'mezcla':
        return [(buscar_creciente, dict(budget=presupuesto, seleccion=seleccion, semilla=semilla))]
    raise ValueError(f'Método sin etapas: {metodo}')


def _heuristica(trips, params, base, metodo, seleccion, semilla, presupuesto):
    plans, intentos, mejoras, motivos = base, 0, 0, []
    for busqueda, opciones in _etapas(metodo, seleccion, semilla, presupuesto):
        plans, _, stats = etapa(plans, trips, params, busqueda, **BUSQUEDA, **opciones)
        intentos += stats.get('intentos', 0)
        mejoras += stats.get('mejoras', 0)
        motivos.append(stats.get('motivo_fin', stats.get('rechazo', '')))
    return plans, dict(intentos=intentos, mejoras=mejoras, motivo_fin='|'.join(motivos))


def _carpeta_planes(planes, instancia, metodo, seleccion, semilla, presupuesto):
    if planes is None:
        return None
    partes = [instancia, metodo] + ([seleccion] if seleccion else []) + ([f's{semilla}'] if seleccion == 'azar' else [])
    return Path(planes) / f"{'_'.join(partes)}_{int(presupuesto)}s"


def _auditar(plans, trips, params, carpeta):
    """Audita el plan; si hay carpeta, además lo exporta (una carpeta sin fila en la tabla quedó incompleta)."""
    if carpeta is None:
        return verificar(plans, trips, *params)[0]
    if carpeta.exists():
        shutil.rmtree(carpeta)
    carpeta.parent.mkdir(parents=True, exist_ok=True)
    return export(carpeta, plans, trips, params)


def correr_uno(trips, params, base, metodo, seleccion, semilla, presupuesto, carpeta=None, hilos_exacta=1):
    tick = time.perf_counter()
    extra = {}
    if metodo == 'solo_base':
        plans = base
    elif metodo in EXACTAS:
        plans, info = resolver_exacto(trips, *params, limit=presupuesto, podar=metodo == 'exacta_podada',
                                      hilos=hilos_exacta)
        extra = dict(optimo=info['optimo'], cota_usd=info.get('cota_usd', ''), motivo_fin=f"estado_{info['estado']}")
        if plans is None:  # sin plan en el tiempo dado: igual se anota la cota inferior
            return dict(extra, tiempo_s=round(time.perf_counter() - tick, 2),
                        error=f"Sin solución en el tiempo dado (estado {info['estado']})")
    else:
        plans, extra = _heuristica(trips, params, base, metodo, seleccion, semilla, presupuesto)
    reporte = _auditar(plans, trips, params, carpeta)
    return dict(buses=reporte['buses'], costo_total_usd=round(reporte['costo_total_usd'], 4), km=round(reporte['km'], 4),
                carga_kwh=round(reporte['carga_kwh'], 4), sesiones=reporte['sesiones'],
                tiempo_s=round(time.perf_counter() - tick, 2), **extra)


def _corridas(metodos, selecciones, semillas):
    for metodo in metodos:
        if metodo in CON_SELECCION:
            for seleccion in selecciones:
                for semilla in (semillas if seleccion == 'azar' else [0]):
                    yield metodo, seleccion, semilla
        else:
            yield metodo, '', 0


def _hechas(salida):
    if not salida.exists():
        return set()
    return {(r['instancia'], r['metodo'], r['seleccion'], int(r['semilla']), float(r['presupuesto_s']))
            for r in read_csv(salida)}


def correr(instancias, metodos, presupuestos, selecciones=('parecidos', 'azar'), semillas=(1, 2, 3),
           salida=None, continuar=False, presupuesto_exacta=None, planes=None, hilos_exacta=1):
    salida = Path(salida)
    if salida.exists() and not continuar:
        raise FileExistsError(f'{salida} ya existe; usa --continuar o elige otro nombre')
    hechas = _hechas(salida) if continuar else set()
    salida.parent.mkdir(parents=True, exist_ok=True)
    nueva = not salida.exists()
    filas = []
    with salida.open('a', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=CAMPOS)
        if nueva:
            writer.writeheader()
        for carpeta in instancias:
            trips, *params = load_instance(carpeta)
            base = solve(trips, *params)[-1] if set(metodos) - EXACTAS else None  # la exacta no lo usa
            for metodo, seleccion, semilla in _corridas(metodos, selecciones, semillas):
                tiempos = [presupuesto_exacta] if metodo in EXACTAS and presupuesto_exacta else presupuestos
                for presupuesto in (tiempos if metodo != 'solo_base' else [0]):
                    clave = (Path(carpeta).name, metodo, seleccion, semilla, float(presupuesto))
                    if clave in hechas:
                        continue
                    fila = dict(zip(('instancia', 'metodo', 'seleccion', 'semilla', 'presupuesto_s'), clave),
                                corridas=len(trips))
                    try:
                        destino = _carpeta_planes(planes, *clave)
                        fila.update(correr_uno(trips, params, base, metodo, seleccion, semilla, presupuesto, destino,
                                               hilos_exacta))
                    except Exception as error:  # se registra y se sigue: la tabla debe decir qué falló
                        fila['error'] = f'{type(error).__name__}: {error}'[:300]
                    writer.writerow({k: fila.get(k, '') for k in CAMPOS})
                    stream.flush()
                    filas.append(fila)
                    print(json.dumps({k: fila.get(k) for k in ('instancia', 'metodo', 'seleccion', 'semilla',
                          'presupuesto_s', 'buses', 'costo_total_usd', 'tiempo_s', 'error')}, ensure_ascii=False),
                          flush=True)
    return filas


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--instancias', type=Path, nargs='*',
                        help='Carpetas de instancias; por omisión, todos los casos de octetos/casos')
    parser.add_argument('--metodos', nargs='*', choices=METODOS, default=list(METODOS))
    parser.add_argument('--presupuestos', type=float, nargs='+', required=True, help='Segundos por método')
    parser.add_argument('--presupuesto-exacta', type=float, help='Segundos para la respuesta perfecta')
    parser.add_argument('--selecciones', nargs='*', choices=('parecidos', 'azar'), default=['parecidos', 'azar'])
    parser.add_argument('--semillas', type=int, nargs='*', default=[1, 2, 3])
    parser.add_argument('--salida', type=Path, required=True)
    parser.add_argument('--continuar', action='store_true')
    parser.add_argument('--hilos-exacta', type=int, default=1, help='Hilos de Gurobi para la respuesta perfecta')
    parser.add_argument('--planes', type=Path, help='Carpeta donde guardar los planes auditados de cada corrida')
    args = parser.parse_args()
    if min(args.presupuestos) <= 0:
        parser.error('Los presupuestos deben ser positivos')
    instancias = args.instancias or sorted(p for p in CASOS.iterdir() if (p / 'escenario.json').exists())
    correr(instancias, args.metodos, args.presupuestos, args.selecciones, args.semillas, args.salida,
           args.continuar, args.presupuesto_exacta, args.planes, args.hilos_exacta)


if __name__ == '__main__':
    main()
