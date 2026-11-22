"""Crea los casos muy chicos y chicos para comparar pares y tríos contra grupos más grandes.

Cada caso es un subconjunto de rutas completas de la instancia de 212 rutas, de un solo sector:
  - 6 muy chicos: 1 ruta de 15 a 40 corridas, donde se puede buscar la respuesta perfecta;
  - 5 chicos: 2, 3 o 4 rutas de 25 a 80 corridas cada una;
  - con --medianos, una escalera de 4 casos de ~200, 250, 300 y 400 corridas de un mismo sector, donde
    cada caso contiene al anterior; sirve para ver hasta dónde llega la respuesta perfecta;
  - con --rutas 6 8 10 12, una escalera por número de rutas en un sector (por omisión el 2), sumando
    primero las rutas con menos corridas; así un caso de 10 rutas queda en ~300 corridas.
Las corridas se copian sin cambios y el horizonte es el de la instancia de origen.

Uso, desde la raíz del proyecto:
  .venv-optimizacion/bin/python 09-entrega3/octetos/crear_casos.py
  .venv-optimizacion/bin/python 09-entrega3/octetos/crear_casos.py --medianos
  .venv-optimizacion/bin/python 09-entrega3/octetos/crear_casos.py --rutas 6 8 10 12 --sector 2
"""
import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from metodo_hibrido.caso_base import load_instance, read_csv, validate_inputs, write_csv  # noqa: E402

INSTANCIA_212 = RAIZ / 'metodo_hibrido/instancia_212'
DESTINO = Path(__file__).resolve().parent / 'casos'

MUY_CHICO_CORRIDAS = (15, 40)
MUY_CHICO_IDEAL = 25
MUY_CHICOS = 6
CHICO_CORRIDAS = (25, 80)
# (número del caso, posición del sector en orden, número de rutas) de cada caso chico. El sector 4
# es el que tiene más rutas en el rango, por eso recibe dos casos.
CHICOS = ((2, 1, 2), (3, 2, 3), (4, 3, 3), (5, 4, 4), (6, 3, 4))
# Escalera de casos medianos: corridas mínimas de cada peldaño y tamaño de las rutas que se suman.
MEDIANOS = (200, 250, 300, 400)
MEDIANO_RUTA_MIN, MEDIANO_RUTA_MAX = 25, 120
MEDIANO_HOLGURA = 0.05


def _rutas(corridas):
    conteo = Counter(r['route_id'] for r in corridas)
    sectores = {}
    for r in corridas:
        if sectores.setdefault(r['route_id'], r['sector_id']) != r['sector_id']:
            raise ValueError(f"La ruta {r['route_id']} aparece en más de un sector")
    return conteo, sectores


def _muy_chicos(conteo, sectores):
    bajo, alto = MUY_CHICO_CORRIDAS
    candidatas = sorted((abs(n - MUY_CHICO_IDEAL), ruta) for ruta, n in conteo.items() if bajo <= n <= alto)
    elegidas = []
    for sector in sorted(set(sectores.values())):
        mejor = next((ruta for _, ruta in candidatas if sectores[ruta] == sector), None)
        if mejor is not None:
            elegidas.append(mejor)
    elegidas += [ruta for _, ruta in candidatas if ruta not in elegidas][:MUY_CHICOS - len(elegidas)]
    if len(elegidas) != MUY_CHICOS:
        raise ValueError(f'Solo hay {len(elegidas)} rutas de {bajo} a {alto} corridas')
    return [dict(tipo='muy_chico', nombre=f'muy_chico_{i:02d}_ruta_{ruta}', sector=sectores[ruta], rutas=[ruta])
            for i, ruta in enumerate(elegidas, 1)]


def _chicos(conteo, sectores, usadas):
    bajo, alto = CHICO_CORRIDAS
    orden = sorted(set(sectores.values()))
    usadas = set(usadas)
    casos = []
    for i, posicion, cuantas in CHICOS:
        sector = orden[posicion]
        libres = sorted(r for r, n in conteo.items()
                        if sectores[r] == sector and bajo <= n <= alto and r not in usadas)
        if len(libres) < cuantas:
            raise ValueError(f'El sector {sector} no tiene {cuantas} rutas libres de {bajo} a {alto} corridas')
        rutas = libres[:cuantas]
        usadas |= set(rutas)
        casos.append(dict(tipo='chico', nombre=f'chico_{i:02d}_sector_{sector}_{cuantas}_rutas',
                          sector=sector, rutas=rutas))
    return casos


def elegir_casos(corridas):
    """Regla fija y reproducible; no depende del orden de las corridas."""
    conteo, sectores = _rutas(corridas)
    muy_chicos = _muy_chicos(conteo, sectores)
    return muy_chicos + _chicos(conteo, sectores, [c['rutas'][0] for c in muy_chicos])


def elegir_medianos(corridas, usadas):
    """Escalera en el sector con más corridas en rutas libres de 25 a 120 corridas.

    Cada peldaño parte del anterior y agrega, de a una, la ruta libre que deja el total más cerca de su
    objetivo (empate: menos corridas, luego nombre), hasta quedar a menos de MEDIANO_HOLGURA de él.
    """
    conteo, sectores = _rutas(corridas)
    usadas = set(usadas)
    por_sector = {}
    for ruta, n in conteo.items():
        if MEDIANO_RUTA_MIN <= n <= MEDIANO_RUTA_MAX and ruta not in usadas:
            por_sector.setdefault(sectores[ruta], {})[ruta] = n
    sector = max(sorted(por_sector), key=lambda s: sum(por_sector[s].values()))
    libres = dict(por_sector[sector])
    rutas, total, casos = [], 0, []
    for objetivo in MEDIANOS:
        while total < objetivo * (1 - MEDIANO_HOLGURA) or not rutas or (casos and rutas == casos[-1]['rutas']):
            if not libres:
                raise ValueError(f'El sector {sector} no alcanza {objetivo} corridas en rutas libres')
            ruta = min(libres, key=lambda r: (abs(total + libres[r] - objetivo), libres[r], r))
            rutas, total = rutas + [ruta], total + libres.pop(ruta)
        casos.append(dict(tipo='mediano', objetivo=objetivo, sector=sector, rutas=list(rutas),
                          nombre=f'mediano_{objetivo}_sector_{sector}_{len(rutas)}_rutas'))
    return casos


def elegir_por_rutas(corridas, sector, cuantas):
    """Escalera de casos de un sector con cuantas[k] rutas: las de menos corridas primero (empate: nombre)."""
    conteo, sectores = _rutas(corridas)
    orden = sorted((n, r) for r, n in conteo.items() if sectores[r] == sector)
    if not orden:
        raise ValueError(f'El sector {sector} no tiene rutas')
    casos = []
    for k in sorted(cuantas):
        if k > len(orden):
            raise ValueError(f'El sector {sector} tiene {len(orden)} rutas; se pidieron {k}')
        rutas = [r for _, r in orden[:k]]
        casos.append(dict(tipo='por_rutas', sector=sector, rutas=rutas, nombre=f'rutas_{k:02d}_sector_{sector}'))
    return casos


def _distancias_del_caso(distancias, paradas):
    """Conserva los pares cuyos extremos de parada pertenecen al caso; terminales y electroterminales, todos."""
    def sirve(extremo):
        return not extremo.startswith('S:') or extremo in paradas
    return [r for r in distancias if sirve(r['origen_id']) and sirve(r['destino_id'])]


def _escribir(carpeta, corridas, distancias, escenario):
    carpeta.mkdir()
    write_csv(carpeta / 'corridas.csv', corridas)
    write_csv(carpeta / 'distancias.csv', distancias)
    (carpeta / 'escenario.json').write_text(json.dumps(escenario, ensure_ascii=False, indent=2), encoding='utf8')
    validate_inputs(*load_instance(carpeta))


def crear_casos(destino=DESTINO, origen=INSTANCIA_212):
    corridas = read_csv(Path(origen) / 'corridas.csv')
    return _crear(elegir_casos(corridas), corridas, Path(destino), Path(origen), 'indice.csv')


def crear_medianos(destino=DESTINO, origen=INSTANCIA_212):
    corridas = read_csv(Path(origen) / 'corridas.csv')
    usadas = {r for c in elegir_casos(corridas) for r in c['rutas']}
    return _crear(elegir_medianos(corridas, usadas), corridas, Path(destino), Path(origen), 'indice_medianos.csv')


def crear_por_rutas(cuantas, sector='2', destino=DESTINO, origen=INSTANCIA_212):
    corridas = read_csv(Path(origen) / 'corridas.csv')
    return _crear(elegir_por_rutas(corridas, sector, cuantas), corridas, Path(destino), Path(origen),
                  f'indice_rutas_sector_{sector}.csv')


def _crear(casos, corridas, destino, origen, nombre_indice):
    existentes = [c['nombre'] for c in casos if (destino / c['nombre']).exists()]
    if existentes or (destino / nombre_indice).exists():
        raise FileExistsError(f'Ya existen casos en {destino}: {existentes[:3]}')
    distancias = read_csv(origen / 'distancias.csv')
    base = json.loads((origen / 'escenario.json').read_text(encoding='utf-8-sig'))
    huella = hashlib.sha256((origen / 'corridas.csv').read_bytes()).hexdigest()
    destino.mkdir(parents=True, exist_ok=True)
    indice = []
    for caso in casos:
        rutas = set(caso['rutas'])
        propias = [r for r in corridas if r['route_id'] in rutas]
        paradas = {'S:' + r[k] for r in propias for k in ('inicio_stop_id', 'fin_stop_id')}
        escenario = {**base, 'rutas': sorted(rutas),
                     'origen': f"Caso {caso['tipo'].replace('_', ' ')} de la instancia de 212 rutas; rutas completas",
                     'corridas_origen_sha256': huella}
        _escribir(destino / caso['nombre'], propias, _distancias_del_caso(distancias, paradas), escenario)
        indice.append(dict(nombre=caso['nombre'], tipo=caso['tipo'], sector=caso['sector'],
                           rutas='|'.join(caso['rutas']), corridas=len(propias)))
    write_csv(destino / nombre_indice, indice)
    return indice


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--destino', type=Path, default=DESTINO)
    parser.add_argument('--medianos', action='store_true', help='crea solo la escalera de casos medianos')
    parser.add_argument('--rutas', type=int, nargs='+', help='crea solo una escalera con estos números de rutas')
    parser.add_argument('--sector', default='2', help='sector de la escalera por número de rutas')
    args = parser.parse_args()
    if args.rutas:
        filas = crear_por_rutas(args.rutas, args.sector, args.destino)
    else:
        filas = (crear_medianos if args.medianos else crear_casos)(args.destino)
    for fila in filas:
        print(f"{fila['nombre']:<34} sector {fila['sector']}  {fila['corridas']:>4} corridas  {fila['rutas']}")


if __name__ == '__main__':
    main()
