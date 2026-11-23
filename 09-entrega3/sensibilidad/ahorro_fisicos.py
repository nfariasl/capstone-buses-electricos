"""Ahorro de cuartetos contra el caso base con la misma batería o el mismo consumo (día laboral).

Lee los planes de cuartetos de resultados/fisicos_417_L.csv (correr_fisicos.sh) y el caso base de cada
escenario (caso_base_fisicos.sh), y escribe resultados/ahorro_fisicos.csv.
Uso: python3 09-entrega3/sensibilidad/ahorro_fisicos.py
"""
import csv
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RES = Path(__file__).resolve().parent / 'resultados'
CASOS_BASE = {
    'instancia_417': RAIZ / 'codigo/output/tres_fases/red_417_L_caso_base',
    **{e: RAIZ / 'codigo/output/tres_fases/sensibilidad_fisicos' / e
       for e in ('bateria_300', 'bateria_250', 'consumo_+10', 'consumo_+20')},
}


def leer_caso_base(carpeta):
    resumen = json.loads((carpeta / 'resumen.json').read_text(encoding='utf-8'))
    base = resumen['caso_base']
    if not base['verificado']:
        raise ValueError(f'Caso base sin verificar: {carpeta}')
    return resumen['configuracion'], base


def variacion(nuevo, viejo):
    return round(100 * (nuevo - viejo) / viejo, 2)


def filas():
    with (RES / 'fisicos_417_L.csv').open(encoding='utf-8-sig') as f:
        planes = {r['instancia']: r for r in csv.DictReader(f) if r['metodo'] == 'cuartetos'}
    for escenario, carpeta in CASOS_BASE.items():
        config, base = leer_caso_base(carpeta)
        plan = planes[escenario]
        if int(plan['corridas']) != base['corridas']:
            raise ValueError(f'{escenario}: el plan y el caso base no cubren las mismas corridas')
        buses, costo = int(plan['buses']), float(plan['costo_total_usd'])
        yield dict(escenario=escenario, bateria_kwh=config['bateria_kwh'], consumo_kwh_km=config['consumo_kwh_km'],
                   buses_caso_base=base['buses'], costo_caso_base_usd=round(base['costo_total_usd']),
                   buses_cuartetos=buses, costo_cuartetos_usd=round(costo),
                   ahorro_buses_pct=variacion(buses, base['buses']),
                   ahorro_costo_pct=variacion(costo, base['costo_total_usd']))


def main():
    resultado = list(filas())
    with (RES / 'ahorro_fisicos.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(resultado[0]))
        w.writeheader()
        w.writerows(resultado)
    for r in resultado:
        print(r)


if __name__ == '__main__':
    main()
