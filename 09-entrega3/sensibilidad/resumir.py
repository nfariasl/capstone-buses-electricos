"""Tabla de sensibilidad: buses, costo y Δ % de cada escenario contra la instancia base, por método.

Lee la tabla que deja correr_sensibilidad.sh y escribe tabla_sensibilidad.csv al lado.
Uso, desde la raíz del proyecto:
    python3 09-entrega3/sensibilidad/resumir.py 09-entrega3/sensibilidad/resultados/sensibilidad_417_L.csv
"""
import argparse
import csv
from pathlib import Path

BASE = 'instancia_417'
CAMPOS = ['escenario', 'metodo', 'buses', 'costo_total_usd', 'delta_buses', 'delta_costo_usd', 'delta_costo_pct',
          'km', 'carga_kwh', 'error']


def resumir(filas):
    """Una fila por escenario y método; el Δ se calcula contra la base con el mismo método."""
    validas = [f for f in filas if not f.get('error') and f.get('costo_total_usd')]
    base = {f['metodo']: f for f in validas if f['instancia'] == BASE}
    salida = []
    for f in filas:
        fila = dict(escenario='base' if f['instancia'] == BASE else f['instancia'], metodo=f['metodo'],
                    buses=f.get('buses', ''), costo_total_usd=f.get('costo_total_usd', ''), km=f.get('km', ''),
                    carga_kwh=f.get('carga_kwh', ''), error=f.get('error', ''))
        ref = base.get(f['metodo'])
        if f in validas and ref is not None:
            costo, costo_ref = float(f['costo_total_usd']), float(ref['costo_total_usd'])
            fila.update(delta_buses=int(f['buses']) - int(ref['buses']),
                        delta_costo_usd=round(costo - costo_ref, 2),
                        delta_costo_pct=round(100 * (costo - costo_ref) / costo_ref, 3))
        salida.append(fila)
    return sorted(salida, key=lambda r: (r['metodo'], r['escenario'] != 'base', r['escenario']))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('tabla', type=Path)
    args = parser.parse_args()
    with args.tabla.open(encoding='utf-8-sig', newline='') as f:
        filas = resumir(list(csv.DictReader(f)))
    destino = args.tabla.parent / 'tabla_sensibilidad.csv'
    with destino.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS)
        w.writeheader()
        w.writerows({k: r.get(k, '') for k in CAMPOS} for r in filas)
    for r in filas:
        print(f"{r['metodo']:<10} {r['escenario']:<20} {r['buses']:>6} {r['costo_total_usd']:>14} "
              f"{r.get('delta_buses', ''):>5} {r.get('delta_costo_pct', '')!s:>8} {r['error']}")
    print(f'→ {destino}')


if __name__ == '__main__':
    main()
