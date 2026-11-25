"""Rutas de los resultados de la Entrega 3 que usa el informe final, y lectura con validación."""
import csv
import os
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
E3 = RAIZ / '09-entrega3'
INFORME = Path(__file__).resolve().parents[1]

OCTETOS = E3 / 'octetos/resultados'
KPI = E3 / 'kpi/resultados'
SENSIBILIDAD = E3 / 'sensibilidad/resultados'
INCERTIDUMBRE = E3 / 'incertidumbre/resultados'
INSTANCIAS = {'L': RAIZ / 'metodo_hibrido/instancia_417',
              'S': RAIZ / 'metodo_hibrido/instancia_417_S',
              'D': RAIZ / 'metodo_hibrido/instancia_417_D'}
CIFRAS_INFORME2 = RAIZ / '08-entrega2/informe2/cifras.tex'

BANDERA_SOLO_NUBE = 0x40000000  # SF_DATALESS de macOS: el contenido está solo en iCloud


def _comprobar(ruta):
    ruta = Path(ruta)
    if not ruta.exists():
        raise FileNotFoundError(f'Falta el archivo fuente: {ruta}')
    if getattr(os.stat(ruta), 'st_flags', 0) & BANDERA_SOLO_NUBE:
        raise OSError(f'Archivo solo en iCloud (marcar «Mantener descargado»): {ruta}')
    return ruta


def leer_csv(ruta):
    """Filas del CSV como diccionarios, sin las filas que registraron un error."""
    with _comprobar(ruta).open(encoding='utf-8-sig', newline='') as archivo:
        filas = list(csv.DictReader(archivo))
    return [f for f in filas if not (f.get('error') or '').strip()]


def leer_texto(ruta):
    return _comprobar(ruta).read_text(encoding='utf-8')


MACRO = re.compile(r'\\newcommand\{\\([A-Za-z]+)\}\{(.*)\}$')


def macros_informe2():
    """Cifras ya generadas por el script del informe 2 (muestra de 212 rutas)."""
    salida = {}
    for linea in leer_texto(CIFRAS_INFORME2).splitlines():
        m = MACRO.match(linea.strip())
        if m:
            salida[m.group(1)] = m.group(2)
    return salida
