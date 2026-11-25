"""Ocupación máxima de los terminales comunes (T01–T04) en el plan y en el caso base, día laboral.

El modelo supone estacionamiento ilimitado en los terminales comunes, porque el enunciado no da su
capacidad (comentario de la corrección del informe 2). Este script mide cuántos buses llegan a estar a
la vez en cada uno, para saber qué capacidad haría falta. Un bus ocupa el terminal mientras espera en él
(actividades «espera» con origen en un terminal común), incluida la espera antes de su primera corrida y
después de la última.

Uso: python3 09-entrega3/kpi/ocupacion_terminales.py
Salida: 09-entrega3/kpi/resultados/ocupacion_terminales.csv
"""
import csv
import sys
from collections import defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
PLANES = {
    'metodo_L': RAIZ / '09-entrega3/octetos/resultados/planes_417_L/instancia_417_cuartetos_azar_s1_2400s/actividades.csv',
    'caso_base_L': RAIZ / 'codigo/output/tres_fases/red_417_L_caso_base/actividades.csv',
}
SALIDA = RAIZ / '09-entrega3/kpi/resultados/ocupacion_terminales.csv'


def ocupacion_maxima(filas):
    """{terminal: (máximo de buses a la vez, segundo en que ocurre)} para las esperas en terminales comunes."""
    eventos = defaultdict(list)
    for r in filas:
        if r['tipo'] == 'espera' and r['origen'].startswith('T') and r['origen'] == r['destino']:
            eventos[r['origen']] += [(int(r['inicio_s']), 1), (int(r['fin_s']), -1)]
    salida = {}
    for terminal, lista in eventos.items():
        lista.sort(key=lambda e: (e[0], e[1]))
        actual, maximo, cuando = 0, 0, None
        for t, delta in lista:
            actual += delta
            if actual > maximo:
                maximo, cuando = actual, t
        salida[terminal] = (maximo, cuando)
    return salida


def main():
    filas_salida = []
    for plan, ruta in PLANES.items():
        with ruta.open(encoding='utf-8-sig', newline='') as archivo:
            maximos = ocupacion_maxima(csv.DictReader(archivo))
        for terminal, (maximo, cuando) in sorted(maximos.items()):
            hora = f'{(cuando // 3600) % 24:02d}:{(cuando % 3600) // 60:02d}'
            filas_salida.append(dict(plan=plan, terminal=terminal, buses_max=maximo, hora=hora))
    with SALIDA.open('w', encoding='utf-8', newline='') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=['plan', 'terminal', 'buses_max', 'hora'])
        escritor.writeheader()
        escritor.writerows(filas_salida)
    for f in filas_salida:
        print(f)
    return 0


if __name__ == '__main__':
    sys.exit(main())
