"""Crea copias de los casos chicos con una batería más chica, para obligar a recargar durante el día.

Con 350 kWh ningún bus de los casos chicos recarga (carga_kwh = 0 en la respuesta perfecta), así que
esos casos no sirven para comparar cómo planifica las recargas cada método. Las copias solo cambian
bateria_kwh en escenario.json; corridas y distancias son las mismas. La reserva se mantiene en 35 kWh.

Para correrlas, la batería se declara con la variable de entorno BATERIA_KWH (ver metodo_hibrido/energia.py);
load_instance rechaza un caso si no coincide.

Uso, desde la raíz del proyecto:
  .venv-optimizacion/bin/python 09-entrega3/octetos/crear_recarga_forzada.py --baterias 100 150
"""
import argparse
import json
import shutil
from pathlib import Path

CASOS = Path(__file__).resolve().parent / 'casos'
RESERVA_KWH = 35


def nombre_variante(caso, bateria):
    return f'bat{int(bateria)}_{caso}'


def crear_variante(origen, destino, bateria):
    if bateria <= RESERVA_KWH:
        raise ValueError(f'La batería ({bateria}) debe superar la reserva ({RESERVA_KWH})')
    if destino.exists():
        raise FileExistsError(f'{destino} ya existe')
    escenario = json.loads((origen / 'escenario.json').read_text(encoding='utf-8-sig'))
    escenario['parametros'] = {**escenario.get('parametros', {}), 'bateria_kwh': bateria}
    escenario['origen'] = f"{escenario.get('origen', '')}; batería de {bateria} kWh (recarga forzada), copia de {origen.name}"
    destino.mkdir(parents=True)
    for archivo in ('corridas.csv', 'distancias.csv'):
        shutil.copy2(origen / archivo, destino / archivo)
    (destino / 'escenario.json').write_text(json.dumps(escenario, ensure_ascii=False, indent=2), encoding='utf8')
    return destino


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--casos', nargs='+', type=Path, help='Carpetas de origen; por omisión, los chico_*')
    parser.add_argument('--baterias', nargs='+', type=int, default=[100, 150])
    args = parser.parse_args()
    origenes = args.casos or sorted(CASOS.glob('chico_*'))
    if not origenes:
        parser.error('No hay casos de origen')
    for origen in origenes:
        for bateria in args.baterias:
            destino = crear_variante(origen, CASOS / nombre_variante(origen.name, bateria), bateria)
            print(destino.name)


if __name__ == '__main__':
    main()
