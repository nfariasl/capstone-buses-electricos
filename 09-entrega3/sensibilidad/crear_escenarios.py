"""Crea instancias de sensibilidad cambiando solo escenario.json (plazas, conexiones y tarifas).

Cada escenario es una copia de la instancia base (corridas.csv y distancias.csv sin cambios) con un
escenario.json modificado y una clave «sensibilidad» que dice qué se cambió. El método híbrido ya lee
plazas, conexiones y tarifas desde escenario.json, así que estos escenarios corren sin tocar su código.

Los escenarios físicos (batería y consumo) además cambian «parametros» en escenario.json y dejan en
«sensibilidad.entorno» las variables BATERIA_KWH, RESERVA_KWH y CONSUMO_KWH_KM con que hay que correrlos
(metodo_hibrido/energia.py las lee; load_instance rechaza un escenario cuyos parámetros no calcen con
ellas). La reserva se mantiene en el 10 % de la batería, como pide el enunciado. Los costos por bus y por
km no se reoptimizan: se evalúan sobre los planes ya hechos (evaluar_costos.py). Velocidad en vacío,
potencia y estado de carga inicial siguen fijos. El caso base (codigo/tres_fases/caso_base.py) toma plazas y tarifas de codigo/, no de
escenario.json, así que para compararlo en estos escenarios también hay que adaptarlo.

Uso, desde la raíz del repositorio, con la instancia completa ya preparada:
    python3 09-entrega3/sensibilidad/crear_escenarios.py --instancia metodo_hibrido/instancia_417 \\
        --destino metodo_hibrido/sensibilidad_417_L

Después, cada escenario se corre como cualquier instancia, por ejemplo:
    python metodo_hibrido/buscar_mejor.py --instancia metodo_hibrido/sensibilidad_417_L/plazas_-20 \\
        --salida metodo_hibrido/resultados/sens_plazas_-20 --presupuesto 600
"""
import argparse
import copy
import csv
import json
import os
import shutil
from collections import Counter
from pathlib import Path

TERMINALES = ['E1', 'E2', 'E3', 'E4', 'E5']
PRECIO_PUNTA = 0.22  # tramos de 14 a 17 h y de 19 a 22 h en codigo/electricity_prices.csv


def _escalar(valores, factor):
    return {e: int(round(v * factor)) for e, v in valores.items()}


def plazas(factor):
    def cambiar(spec, _):
        spec['capacidad_fisica'] = _escalar(spec['capacidad_fisica'], factor)
        spec['conexiones'] = _escalar(spec['conexiones'], factor)
        return f'Plazas y conexiones de cada electroterminal × {factor:g}'
    return cambiar


def conexiones(factor):
    def cambiar(spec, _):
        spec['conexiones'] = _escalar(spec['conexiones'], factor)
        return f'Conexiones de carga × {factor:g}, mismas plazas'
    return cambiar


def cierre(e):
    def cambiar(spec, _):
        spec['capacidad_fisica'][e] = 0
        spec['conexiones'][e] = 0
        return f'{e} cerrado: 0 plazas y 0 conexiones'
    return cambiar


def tarifa_punta(factor):
    def cambiar(spec, _):
        spec['tarifas'] = [[ini, fin, round(p * factor, 6) if p >= PRECIO_PUNTA - 1e-9 else p]
                           for ini, fin, p in spec['tarifas']]
        return f'Precio de los tramos de punta (USD {PRECIO_PUNTA}/kWh) × {factor:g}'
    return cambiar


def redistribuir(spec, corridas):
    """Mismas plazas totales, repartidas en proporción a las corridas de cada sector (sector k ↔ Ek)."""
    total = sum(spec['capacidad_fisica'].values())
    conteo = Counter(f"E{fila['sector_id']}" for fila in corridas)
    n = sum(conteo[e] for e in TERMINALES)
    exactas = {e: total * conteo[e] / n for e in TERMINALES}
    nuevas = {e: int(exactas[e]) for e in TERMINALES}
    for e in sorted(TERMINALES, key=lambda e: exactas[e] - nuevas[e], reverse=True)[:total - sum(nuevas.values())]:
        nuevas[e] += 1  # restos mayores, para conservar el total
    spec['capacidad_fisica'] = nuevas
    spec['conexiones'] = dict(nuevas)
    return f'Las {total} plazas repartidas según las corridas de cada sector: {nuevas}'


def fisico(parametros, entorno, texto):
    def cambiar(spec, _):
        spec['parametros'] = {**spec.get('parametros', {}), **parametros}
        return texto
    cambiar.entorno = entorno
    return cambiar


ESCENARIOS = {
    'plazas_-20': plazas(0.8),
    'plazas_+20': plazas(1.2),
    'plazas_+50': plazas(1.5),
    'conexiones_-50': conexiones(0.5),
    **{f'cierre_{e}': cierre(e) for e in TERMINALES},
    'tarifa_punta_+50': tarifa_punta(1.5),
    'plazas_por_demanda': redistribuir,
    'bateria_300': fisico({'bateria_kwh': 300, 'reserva_kwh': 30}, {'BATERIA_KWH': '300', 'RESERVA_KWH': '30'},
                          'Batería de 300 kWh (−14 %), reserva de 30 kWh (10 %)'),
    'bateria_250': fisico({'bateria_kwh': 250, 'reserva_kwh': 25}, {'BATERIA_KWH': '250', 'RESERVA_KWH': '25'},
                          'Batería de 250 kWh (−29 %), reserva de 25 kWh (10 %)'),
    'consumo_+10': fisico({'consumo_kwh_km': 1.54}, {'CONSUMO_KWH_KM': '1.54'}, 'Consumo de 1,54 kWh/km (+10 %)'),
    'consumo_+20': fisico({'consumo_kwh_km': 1.68}, {'CONSUMO_KWH_KM': '1.68'}, 'Consumo de 1,68 kWh/km (+20 %)'),
}


def _copiar(origen, destino):
    """Enlace duro si se puede (las distancias de la red completa pesan); si no, copia."""
    try:
        os.link(origen, destino)
    except OSError:
        shutil.copy2(origen, destino)


def crear(instancia, destino, nombres=None):
    instancia, destino = Path(instancia), Path(destino)
    spec = json.loads((instancia / 'escenario.json').read_text(encoding='utf-8-sig'))
    with (instancia / 'corridas.csv').open(encoding='utf-8-sig', newline='') as f:
        corridas = list(csv.DictReader(f))
    destino.mkdir(parents=True, exist_ok=True)
    filas = []
    for nombre in nombres or ESCENARIOS:
        carpeta = destino / nombre
        if carpeta.exists():
            raise FileExistsError(f'{carpeta} ya existe; borra la carpeta o elige otro destino')
        carpeta.mkdir()
        for archivo in ('corridas.csv', 'distancias.csv'):
            _copiar(instancia / archivo, carpeta / archivo)
        nuevo = copy.deepcopy(spec)
        descripcion = ESCENARIOS[nombre](nuevo, corridas)
        nuevo['sensibilidad'] = dict(escenario=nombre, descripcion=descripcion, instancia_base=str(instancia),
                                     entorno=getattr(ESCENARIOS[nombre], 'entorno', {}))
        (carpeta / 'escenario.json').write_text(json.dumps(nuevo, ensure_ascii=False, indent=2), encoding='utf-8')
        filas.append(dict(escenario=nombre, descripcion=descripcion,
                          plazas=json.dumps(nuevo['capacidad_fisica']), conexiones=json.dumps(nuevo['conexiones'])))
    indice = destino / 'indice.csv'   # se conservan las filas de los escenarios creados antes
    nuevos = {f['escenario'] for f in filas}
    previas = [r for r in csv.DictReader(indice.open(encoding='utf-8'))] if indice.exists() else []
    with indice.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows([r for r in previas if r['escenario'] not in nuevos] + filas)
    return filas


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--instancia', type=Path, required=True, help='Carpeta con corridas.csv, distancias.csv y escenario.json')
    parser.add_argument('--destino', type=Path, required=True)
    parser.add_argument('--escenarios', nargs='*', choices=list(ESCENARIOS), help='Por omisión, todos')
    args = parser.parse_args()
    for fila in crear(args.instancia, args.destino, args.escenarios):
        print(f"{fila['escenario']}: {fila['descripcion']}")


if __name__ == '__main__':
    main()
