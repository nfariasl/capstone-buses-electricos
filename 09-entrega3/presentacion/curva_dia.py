"""Viajes en curso a cada hora del día, por tipo de día, para la lámina 5 del deck.

Cuenta, cada 5 minutos, cuántas corridas están en curso (inicio <= t < fin) en la Fase 1
(codigo/output/fase1/corridas.csv) y escribe datos_dia.js. El máximo del día laboral es la cota
básica de flota (6.601 a las 08:00): ningún plan puede usar menos buses que viajes simultáneos.

Uso, desde la raíz del repositorio:
    python3 09-entrega3/presentacion/curva_dia.py
"""
import bisect
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / 'mapa_sectores'))
import datos_geo  # noqa: E402

PASO_S = 300          # una muestra cada 5 minutos
HORIZONTE_S = 26 * 3600
DIAS = ('L', 'S', 'D')


def main():
    corridas = datos_geo.leer_csv(datos_geo.carpeta_codigo() / 'output/fase1/corridas.csv')
    inicios = {d: [] for d in DIAS}
    fines = {d: [] for d in DIAS}
    for fila in corridas:
        inicios[fila['service_id']].append(int(fila['inicio_s']))
        fines[fila['service_id']].append(int(fila['fin_s']))
    datos = {'paso_min': PASO_S // 60, 'corridas': {}, 'curvas': {}, 'picos': {}}
    for d in DIAS:
        ini, fin = sorted(inicios[d]), sorted(fines[d])
        # en curso en t: empezaron en t o antes y todavía no terminan
        curva = [bisect.bisect_right(ini, t) - bisect.bisect_right(fin, t) for t in range(0, HORIZONTE_S + 1, PASO_S)]
        maximo = max(curva)
        t = curva.index(maximo) * PASO_S
        datos['corridas'][d] = len(ini)
        datos['curvas'][d] = curva
        datos['picos'][d] = {'buses': maximo, 'hora': f'{t // 3600:02d}:{t % 3600 // 60:02d}'}
    salida = AQUI / 'datos_dia.js'
    salida.write_text('// Generado por curva_dia.py. No editar a mano.\nconst DIA = ' +
                      json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    print({d: datos['picos'][d] for d in DIAS}, f'→ {salida.name}')


if __name__ == '__main__':
    main()
