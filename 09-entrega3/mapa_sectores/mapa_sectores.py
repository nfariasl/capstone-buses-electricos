"""Dibuja el mapa de Santiago dividido en los cinco sectores del modelo.

Uso:  python3 mapa_sectores.py
Escribe mapa_sectores.pdf y mapa_sectores.png junto a este archivo.

Un sector es un grupo de rutas, no un territorio. Para mostrarlo como mapa se
pinta cada punto de la ciudad con el color del sector al que pertenece la
mayoría de los kilómetros de ruta que pasan cerca.
"""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.patheffects as efectos
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection
from matplotlib.colors import to_rgb
from matplotlib.path import Path as Trazo

import datos_geo
import zonas

AQUI = Path(__file__).resolve().parent
CAJA_GRADOS = (-70.95, -70.40, -33.72, -33.24)  # xmin, xmax, ymin, ymax: Gran Santiago

# Paleta validada con el validador de daltonismo: todos los sectores vecinos se distinguen.
COLOR_SECTOR = {1: '#e34948', 2: '#2a78d6', 3: '#1baf7a', 4: '#eda100', 5: '#008300'}
TINTA, TINTA_SUAVE, BORDE_COMUNA = '#1a1a1a', '#555555', '#4d4d4d'

PASO_KM = 0.1            # cada punto densificado representa 100 m de ruta
CELDA_KM = 0.1
SIGMA_KM = 0.6           # suavizado: una ruta "tiñe" cerca de 1 km a cada lado
UMBRAL_DENSIDAD = 0.02
MAYORIA = 0.5            # sobre esto, el sector predomina con claridad
ALFA_CLARO, ALFA_MEZCLA = 0.82, 0.40
MARGEN_KM = 1.5
MIN_PUNTOS_COMUNA = 400  # comunas con menos ruta que esto no llevan nombre
ANCHO_CM, ALTO_CM = 17.0, 13.3
CM = 1 / 2.54

ABREVIATURAS = {'Pedro Aguirre Cerda': 'P. Aguirre\nCerda', 'Estación Central': 'Estación\nCentral',
                'Quinta Normal': 'Quinta\nNormal', 'San Joaquín': 'San\nJoaquín', 'San Miguel': 'San\nMiguel',
                'La Cisterna': 'La\nCisterna', 'San Ramón': 'San\nRamón', 'La Granja': 'La\nGranja',
                'Independencia': 'Indepen-\ndencia', 'Lo Espejo': 'Lo\nEspejo', 'Cerro Navia': 'Cerro Navia',
                'Lo Barnechea': 'Lo Barnechea', 'Padre Hurtado': 'Padre\nHurtado'}
# Desplazamiento (km) de la etiqueta de cada electroterminal para que no tape el punto.
DESPLAZAMIENTO_ETIQUETA = {1: (0.9, 1.4, 'left'), 2: (-5.2, 2.9, 'right'), 3: (-1.0, 1.1, 'right'),
                           4: (0.9, 1.4, 'left'), 5: (3.6, -3.6, 'left')}
# Corrimiento (km) de nombres de comunas que chocarían con un electroterminal o su etiqueta.
AJUSTE_COMUNA = {'Conchalí': (0.2, -1.0), 'San Ramón': (-0.4, -1.1), 'La Granja': (0.8, 0.3),
                 'Quinta Normal': (0.0, -0.3), 'Lo Espejo': (0.0, -0.6)}
HALO = [efectos.withStroke(linewidth=1.6, foreground='white', alpha=0.85)]


def cargar():
    codigo = datos_geo.carpeta_codigo()
    corridas = datos_geo.leer_csv(codigo / 'output/fase1/corridas.csv')
    return dict(
        sectores=datos_geo.leer_sectores(codigo / 'output/fase1/sectores.csv'),
        formas_ruta=datos_geo.trazados_por_ruta(corridas),
        trazados=datos_geo.leer_trazados(datos_geo.RAIZ / '01-datos/gtfs/shapes.txt'),
        terminales=datos_geo.leer_electroterminales(datos_geo.RAIZ / '01-datos/depots.csv'),
        comunas=datos_geo.leer_comunas(datos_geo.RAIZ / '01-datos/chile.gpkg', CAJA_GRADOS),
    )


def lineas_por_sector(datos):
    """Trazados en km de todas las rutas, agrupados por sector."""
    lineas = {sector: [] for sector in COLOR_SECTOR}
    for ruta, sector in datos['sectores'].items():
        if ruta not in datos['formas_ruta']:
            raise ValueError(f'La ruta {ruta} tiene sector pero no tiene trazado')
        lineas[sector].extend(zonas.a_km(datos['trazados'][forma]) for forma in sorted(datos['formas_ruta'][ruta]))
    return lineas


def caja_del_mapa(puntos_por_sector):
    todos = np.vstack(list(puntos_por_sector.values()))
    (xmin, ymin), (xmax, ymax) = todos.min(axis=0), todos.max(axis=0)
    return (xmin - MARGEN_KM, xmax + MARGEN_KM, ymin - MARGEN_KM, ymax + MARGEN_KM)


def imagen_zonas(resultado):
    """Imagen RGBA: color del sector que predomina, más pálido donde se mezclan varios."""
    alto, ancho = resultado.dominante.shape
    imagen = np.zeros((alto, ancho, 4))
    for sector, color in COLOR_SECTOR.items():
        mascara = resultado.dominante == sector
        imagen[mascara, :3] = to_rgb(color)
        imagen[mascara, 3] = np.where(resultado.participacion[mascara] >= MAYORIA, ALFA_CLARO, ALFA_MEZCLA)
    return imagen


def dibujar_comunas(eje, comunas, ancho, alfa):
    bordes = [zonas.a_km(poligono[0]) for _, poligonos in comunas for poligono in poligonos]
    eje.add_collection(LineCollection(bordes, colors=BORDE_COMUNA, linewidths=ancho, alpha=alfa, zorder=4))


def nombrar_comunas(eje, comunas, puntos_ruta):
    """Escribe cada nombre en el centro de la parte de la comuna por donde pasan rutas."""
    for nombre, poligonos in comunas:
        dentro = np.zeros(len(puntos_ruta), dtype=bool)
        for poligono in poligonos:
            dentro |= Trazo(zonas.a_km(poligono[0])).contains_points(puntos_ruta)
        if dentro.sum() < MIN_PUNTOS_COMUNA:
            continue
        dx, dy = AJUSTE_COMUNA.get(nombre, (0.0, 0.0))
        x, y = np.median(puntos_ruta[dentro], axis=0) + (dx, dy)
        eje.text(x, y, ABREVIATURAS.get(nombre, nombre), fontsize=5.0, color=TINTA, ha='center', va='center',
                 linespacing=0.9, zorder=6, path_effects=HALO)


def dibujar_terminales(eje, terminales, con_nombre):
    for terminal in terminales:
        x, y = zonas.a_km([(terminal['lon'], terminal['lat'])])[0]
        eje.plot(x, y, 'o', ms=8.5 if con_nombre else 4.5, mfc='white', mec=TINTA, mew=1.3 if con_nombre else 0.8, zorder=9)
        if not con_nombre:
            continue
        eje.text(x, y - 0.03, str(terminal['sector']), fontsize=6.2, fontweight='bold', color=TINTA,
                 ha='center', va='center', zorder=10)
        dx, dy, alineado = DESPLAZAMIENTO_ETIQUETA[terminal['sector']]
        eje.annotate(terminal['nombre'], (x, y), xytext=(x + dx, y + dy), fontsize=6.6, fontweight='bold',
                     color=TINTA, ha=alineado, va='center', zorder=10,
                     bbox=dict(boxstyle='round,pad=0.22', fc='white', ec=TINTA, lw=0.6),
                     arrowprops=dict(arrowstyle='-', color=TINTA, lw=0.7, shrinkA=0, shrinkB=4,
                                     relpos=(0.0 if alineado == 'left' else 1.0, 0.5)))


def dibujar_escala(eje, caja):
    x0, y0 = caja[0] + 1.5, caja[2] + 1.6
    eje.plot([x0, x0 + 5], [y0, y0], color=TINTA, lw=1.6, solid_capstyle='butt', zorder=9)
    eje.text(x0 + 2.5, y0 + 0.5, '5 km', fontsize=6, color=TINTA, ha='center', va='bottom', zorder=9)
    xn, yn = caja[0] + 2.2, caja[3] - 2.0
    eje.annotate('', (xn, yn + 1.0), xytext=(xn, yn - 1.4), arrowprops=dict(arrowstyle='-|>', color=TINTA, lw=1.0))
    eje.text(xn, yn - 2.0, 'N', fontsize=6.5, fontweight='bold', color=TINTA, ha='center', va='center')


def preparar_eje(eje, caja, titulo):
    eje.set_xlim(caja[0], caja[1])
    eje.set_ylim(caja[2], caja[3])
    eje.set_aspect('equal')
    eje.set_xticks([])
    eje.set_yticks([])
    for lado in eje.spines.values():
        lado.set_edgecolor('#b5b5b5')
        lado.set_linewidth(0.6)
    eje.set_title(titulo, fontsize=7.6, fontweight='bold', color=TINTA, loc='left', pad=4)


def panel_zonas(eje, datos, resultado, puntos_ruta, caja):
    preparar_eje(eje, caja, 'Qué sector predomina en cada parte de Santiago')
    eje.imshow(imagen_zonas(resultado), origin='lower', extent=resultado.caja_km, interpolation='nearest', zorder=2)
    centros_x = np.linspace(resultado.caja_km[0], resultado.caja_km[1], resultado.dominante.shape[1])
    centros_y = np.linspace(resultado.caja_km[2], resultado.caja_km[3], resultado.dominante.shape[0])
    for sector in COLOR_SECTOR:
        eje.contour(centros_x, centros_y, (resultado.dominante == sector).astype(float), levels=[0.5],
                    colors='white', linewidths=1.1, zorder=3)
    dibujar_comunas(eje, datos['comunas'], ancho=0.35, alfa=0.55)
    nombrar_comunas(eje, datos['comunas'], puntos_ruta)
    dibujar_terminales(eje, datos['terminales'], con_nombre=True)
    dibujar_escala(eje, caja)


def panel_rutas(eje, datos, lineas, caja):
    preparar_eje(eje, caja, f'Las {len(datos["sectores"])} rutas, pintadas por sector')
    dibujar_comunas(eje, datos['comunas'], ancho=0.25, alfa=0.3)
    for sector, color in COLOR_SECTOR.items():
        eje.add_collection(LineCollection(lineas[sector], colors=color, linewidths=0.32, alpha=0.75, zorder=5))
    dibujar_terminales(eje, datos['terminales'], con_nombre=False)


def panel_leyenda(eje, datos, resumen):
    eje.axis('off')
    eje.set_xlim(0, 1)
    eje.set_ylim(0, 1)
    eje.text(0, 0.97, 'Sector (nombre de su electroterminal)', fontsize=6.8, fontweight='bold', color=TINTA, va='top')
    for indice, terminal in enumerate(datos['terminales']):
        y = 0.83 - indice * 0.115
        sector = terminal['sector']
        eje.add_patch(plt.Rectangle((0, y - 0.035), 0.075, 0.07, color=COLOR_SECTOR[sector], alpha=ALFA_CLARO, lw=0))
        eje.text(0.105, y, f'{sector} · {terminal["nombre"]}', fontsize=6.8, color=TINTA, va='center')
        eje.text(0.98, y, f'{resumen[sector]["rutas"]} rutas', fontsize=6.8, color=TINTA_SUAVE, va='center', ha='right')
    y = 0.83 - 5 * 0.115 - 0.02
    for indice, color in enumerate(COLOR_SECTOR.values()):
        eje.add_patch(plt.Rectangle((indice * 0.015, y - 0.035), 0.015, 0.07, color=color, alpha=ALFA_MEZCLA, lw=0))
    eje.text(0.105, y, 'Tono pálido, zona de mezcla donde ningún\nsector reúne la mitad de las rutas',
             fontsize=6.2, color=TINTA_SUAVE, va='center', linespacing=1.05)
    y -= 0.15
    eje.plot(0.037, y, 'o', ms=7, mfc='white', mec=TINTA, mew=1.0)
    eje.text(0.105, y, 'Electroterminal, donde cargan los buses', fontsize=6.2, color=TINTA_SUAVE, va='center')


def main():
    plt.rcParams['font.family'] = ['Arial', 'Helvetica', 'DejaVu Sans']
    datos = cargar()
    lineas = lineas_por_sector(datos)
    puntos = {sector: np.vstack([zonas.densificar(linea, PASO_KM) for linea in lista]) for sector, lista in lineas.items()}
    caja = caja_del_mapa(puntos)
    resultado = zonas.zonas_dominantes(puntos, caja, CELDA_KM, SIGMA_KM, UMBRAL_DENSIDAD)
    resumen = datos_geo.resumen_por_sector(datos_geo.leer_csv(datos_geo.carpeta_codigo() / 'output/fase1/corridas.csv'), dia='L')

    figura = plt.figure(figsize=(ANCHO_CM * CM, ALTO_CM * CM))
    eje_zonas = figura.add_axes([0.005, 0.005, 0.635, 0.955])
    eje_rutas = figura.add_axes([0.655, 0.485, 0.34, 0.475], anchor='N')
    eje_leyenda = figura.add_axes([0.66, 0.02, 0.335, 0.40])
    panel_zonas(eje_zonas, datos, resultado, np.vstack(list(puntos.values()))[::3], caja)
    panel_rutas(eje_rutas, datos, lineas, caja)
    panel_leyenda(eje_leyenda, datos, resumen)
    for extension in ('pdf', 'png'):
        figura.savefig(AQUI / f'mapa_sectores.{extension}', dpi=300)
    print('Mapa escrito en', AQUI / 'mapa_sectores.pdf')


if __name__ == '__main__':
    main()
