"""Trazados de las 417 rutas, comunas y electroterminales como datos SVG para el deck.

Lee lo mismo que 09-entrega3/mapa_sectores/mapa_sectores.py (corridas de la Fase 1, sectores, shapes del GTFS,
depots.csv y comunas de chile.gpkg) y escribe datos_mapa.js con trazados ya proyectados y simplificados,
para dibujarlos y animarlos en el navegador.

Uso, desde la raíz del repositorio:
    python3 09-entrega3/presentacion/mapa_svg.py
"""
import json
import math
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / 'mapa_sectores'))
import datos_geo  # noqa: E402

CAJA_GRADOS = (-70.95, -70.40, -33.72, -33.24)  # la misma caja del mapa de sectores
ANCHO_PX = 1000                                  # ancho del sistema de coordenadas del SVG
MARGEN_PX = 12
TOLERANCIA_PX = 1.2                              # simplificación Douglas-Peucker


def proyectar(caja):
    lon0, lon1, lat0, lat1 = caja
    escala_lon = math.cos(math.radians((lat0 + lat1) / 2))
    factor = (ANCHO_PX - 2 * MARGEN_PX) / ((lon1 - lon0) * escala_lon)
    alto = (lat1 - lat0) * factor + 2 * MARGEN_PX

    def a_px(lon, lat):
        return (MARGEN_PX + (lon - lon0) * escala_lon * factor, MARGEN_PX + (lat1 - lat) * factor)
    return a_px, round(alto)


def simplificar(puntos, tolerancia):
    """Douglas-Peucker iterativo."""
    if len(puntos) < 3:
        return puntos
    mantener = [False] * len(puntos)
    mantener[0] = mantener[-1] = True
    pila = [(0, len(puntos) - 1)]
    while pila:
        a, b = pila.pop()
        (xa, ya), (xb, yb) = puntos[a], puntos[b]
        dx, dy = xb - xa, yb - ya
        largo = math.hypot(dx, dy) or 1e-9
        peor, indice = 0.0, None
        for i in range(a + 1, b):
            x, y = puntos[i]
            d = abs(dy * (x - xa) - dx * (y - ya)) / largo
            if d > peor:
                peor, indice = d, i
        if indice is not None and peor > tolerancia:
            mantener[indice] = True
            pila += [(a, indice), (indice, b)]
    return [p for p, m in zip(puntos, mantener) if m]


def raleo(puntos, minimo):
    """Descarta puntos a menos de `minimo` px del último conservado; deja el DP en tiempo razonable."""
    if not puntos:
        return puntos
    salida = [puntos[0]]
    for x, y in puntos[1:]:
        if math.hypot(x - salida[-1][0], y - salida[-1][1]) >= minimo:
            salida.append((x, y))
    if salida[-1] != puntos[-1]:
        salida.append(puntos[-1])
    return salida


def camino(puntos_px):
    pts = simplificar(raleo(puntos_px, TOLERANCIA_PX / 2), TOLERANCIA_PX)
    return 'M' + 'L'.join(f'{x:.1f},{y:.1f}' for x, y in pts)


def main():
    codigo = datos_geo.carpeta_codigo()
    corridas = datos_geo.leer_csv(codigo / 'output/fase1/corridas.csv')
    sectores = datos_geo.leer_sectores(codigo / 'output/fase1/sectores.csv')
    formas_ruta = datos_geo.trazados_por_ruta(corridas)
    trazados = datos_geo.leer_trazados(datos_geo.RAIZ / '01-datos/gtfs/shapes.txt')
    terminales = datos_geo.leer_electroterminales(datos_geo.RAIZ / '01-datos/depots.csv')
    # Las comunas salen de chile.gpkg (1,4 GB) y leerlas tarda varios minutos; solo se leen con --comunas.
    comunas = (datos_geo.leer_comunas(datos_geo.RAIZ / '01-datos/chile.gpkg', CAJA_GRADOS)
               if '--comunas' in sys.argv else [])
    a_px, alto = proyectar(CAJA_GRADOS)

    rutas = []
    for ruta, sector in sorted(sectores.items()):
        if ruta not in formas_ruta:
            raise ValueError(f'La ruta {ruta} tiene sector pero no tiene trazado')
        for forma in sorted(formas_ruta[ruta]):
            rutas.append({'r': ruta, 's': sector, 'd': camino([a_px(lon, lat) for lon, lat in trazados[forma]])})
    contornos = []
    for _nombre, poligonos in comunas:
        for poligono in poligonos:          # cada polígono es una lista de anillos; basta el exterior
            contornos.append(camino([a_px(lon, lat) for lon, lat in poligono[0]]) + 'Z')
    puntos = []
    for t in terminales:
        x, y = a_px(t['lon'], t['lat'])
        puntos.append(dict(nombre=t['nombre'], plazas=t['plazas'], sector=t['sector'], x=round(x, 1), y=round(y, 1)))

    datos = dict(ancho=ANCHO_PX, alto=alto, rutas=rutas, comunas=contornos, electroterminales=puntos,
                 n_rutas=len(sectores))
    salida = AQUI / 'datos_mapa.js'
    salida.write_text('// Generado por mapa_svg.py. No editar a mano.\nconst MAPA = ' +
                      json.dumps(datos, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
    print(f'{len(sectores)} rutas, {len(rutas)} trazados, {len(contornos)} contornos; '
          f'{salida.stat().st_size / 1024:.0f} KB en {salida.name}')


if __name__ == '__main__':
    main()
