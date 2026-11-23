"""Convierte deck.html en un .pptx editable para importarlo en Canva y seguir trabajando en grupo.

Cada paso de cada lámina pasa a ser una página, armada en capas:
  1. fondo: captura del paso sin textos, sin íconos, sin encabezado y sin línea de recorrido
     (quedan los gráficos, los mapas y la foto);
  2. íconos: cada uno como imagen PNG transparente, movible y copiable;
  3. textos: cuadros editables con su tipografía, tamaño y color (incluido el encabezado ICS2122);
  4. línea de recorrido: formas nativas agrupadas (línea, paradas, tramos y el marcador «n / 20»).
Las notas del orador van en cada página. Al final se agregan páginas de kit para el grupo: guía de estilo,
hoja de íconos, plantilla de lámina y un gráfico nativo de ejemplo. Además se guardan los íconos en SVG.

Requiere el servidor del deck (preview "deck-final": http://localhost:8765), Google Chrome, python-pptx y Pillow.

Uso, desde la raíz del repositorio:
    python3 09-entrega3/presentacion/exportar_pptx.py            # todo el deck + kit
    python3 09-entrega3/presentacion/exportar_pptx.py --desde 12 # solo las láminas 12 en adelante
"""
import csv
import json
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Emu, Pt

AQUI = Path(__file__).resolve().parent
URL = 'http://localhost:8765/deck.html'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
TRABAJO = AQUI / 'exportacion'
CARPETA_SVG = AQUI / 'iconos'
SALIDA = AQUI / 'presentacion_final_G29.pptx'
EMU_POR_PX = 6350            # lámina de 13,333 × 7,5 pulgadas = 1920 × 1080 px → 144 px por pulgada
INTERLINEADO_SIMPLE = 1.2    # interlineado «simple» de PowerPoint, en veces el tamaño de la fuente
REINTENTOS = 3
HOLGURA_ANCHO = 1.06         # Canva mide el texto un poco distinto: margen para que no salte de línea
LADO_ICONO_PX = 256          # resolución de cada ícono PNG
ALINEACION = {'left': PP_ALIGN.LEFT, 'start': PP_ALIGN.LEFT, 'center': PP_ALIGN.CENTER,
              'right': PP_ALIGN.RIGHT, 'end': PP_ALIGN.RIGHT}
DISPLAY, SERIF = 'Overpass', 'Source Serif 4'


# ---------------------------------------------------------------- lectura del deck (fuente única)
def deck():
    return (AQUI / 'deck.html').read_text(encoding='utf-8')


def paginas():
    """(número de lámina, cantidad de pasos) en el orden del deck."""
    resultado = []
    for atributos in re.findall(r'<section class="lamina[^"]*" ([^>]*)>', deck()):
        n = int(re.search(r'data-n="(\d+)"', atributos).group(1))
        pasos = re.search(r'data-pasos="(\d+)"', atributos)
        resultado.append((n, int(pasos.group(1)) if pasos else 1))
    return resultado


def tokens():
    """Colores de :root del deck, p. ej. {'rojo': '#CF152D', ...}."""
    raiz = re.search(r':root \{(.*?)\n\}', deck(), re.S).group(1)
    return {nombre: valor.upper() for nombre, valor in re.findall(r'--([\w-]+):\s*(#[0-9A-Fa-f]{6})', raiz)}


def iconos_del_deck():
    bloque = re.search(r'const ICONOS = \{(.*?)\n\};', deck(), re.S).group(1)
    return dict(re.findall(r'^\s*"?([\w-]+)"?:\s*"([^"]+)",?$', bloque, re.M))


def recorrido_del_deck():
    texto = deck()
    total = int(re.search(r'const TOTAL = (\d+);', texto).group(1))
    bloques = [(nombre, int(desde)) for nombre, desde in re.findall(r'\{ nombre: "([^"]+)", desde: (\d+) \}', texto)]
    return total, bloques


# ---------------------------------------------------------------- capturas con Chrome sin ventana
def chrome(*argumentos, ventana='1920,1080'):
    perfil = tempfile.mkdtemp(prefix='chrome_deck_')   # un perfil por llamada: varias instancias en paralelo
    base = [CHROME, '--headless=new', '--disable-gpu', '--hide-scrollbars', f'--window-size={ventana}',
            '--virtual-time-budget=7000', f'--user-data-dir={perfil}']
    try:
        return subprocess.run(base + list(argumentos), capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return None
    finally:
        shutil.rmtree(perfil, ignore_errors=True)


def capturar(n, paso):
    """Fondo (PNG) y medidas de textos e íconos (JSON) de un paso; reintenta si Chrome falla."""
    png = TRABAJO / f'{n:02d}_{paso}.png'
    for intento in range(REINTENTOS):
        png.unlink(missing_ok=True)
        chrome(f'--screenshot={png}', f'{URL}?exportar&sintexto&sinmarco&siniconos#{n}.{paso}')
        dom = chrome('--dump-dom', f'{URL}?exportar&medir=3500#{n}.{paso}')
        m = dom and re.search(r'<script type="application/json" id="medidas">(.*?)</script>', dom.stdout, re.S)
        if png.exists() and m:
            break
        print(f'  reintento {intento + 1} en la lámina {n}, paso {paso}', flush=True)
    else:
        raise RuntimeError(f'No se pudo capturar la lámina {n}, paso {paso}')
    medidas = json.loads(m.group(1))
    if (medidas['n'], medidas['paso']) != (n, paso):
        raise RuntimeError(f'Se midió {medidas["n"]}.{medidas["paso"]} en vez de {n}.{paso}')
    return png, medidas


def hex_de(css):
    if css.startswith('#'):
        return css.upper()
    r, g, b = (int(float(v)) for v in re.findall(r'[\d.]+', css)[:3])
    return f'#{r:02X}{g:02X}{b:02X}'


def rasterizar_iconos(combinaciones, trazos):
    """PNG transparente para cada (ícono, color), recortados de una sola hoja renderizada por Chrome."""
    combinaciones = sorted(combinaciones)
    columnas = 8
    filas = -(-len(combinaciones) // columnas)
    celdas = ''.join(
        f'<svg width="{LADO_ICONO_PX}" height="{LADO_ICONO_PX}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="display:block;float:left">'
        f'<path d="{trazos[ico]}"/></svg>'
        for ico, color in combinaciones)
    hoja = TRABAJO / 'hoja_iconos.html'
    hoja.write_text(f'<!doctype html><html><body style="margin:0;background:transparent;'
                    f'width:{columnas * LADO_ICONO_PX}px">{celdas}</body></html>', encoding='utf-8')
    imagen = TRABAJO / 'hoja_iconos.png'
    imagen.unlink(missing_ok=True)
    chrome('--default-background-color=00000000', f'--screenshot={imagen}', hoja.as_uri(),
           ventana=f'{columnas * LADO_ICONO_PX},{filas * LADO_ICONO_PX}')
    hoja_png = Image.open(imagen)
    carpeta = TRABAJO / 'iconos'
    carpeta.mkdir(exist_ok=True)
    rutas = {}
    for i, (ico, color) in enumerate(combinaciones):
        x, y = (i % columnas) * LADO_ICONO_PX, (i // columnas) * LADO_ICONO_PX
        ruta = carpeta / f'{ico}_{color[1:]}.png'
        hoja_png.crop((x, y, x + LADO_ICONO_PX, y + LADO_ICONO_PX)).save(ruta)
        rutas[(ico, color)] = ruta
    return rutas


def guardar_svg(trazos, color):
    """Íconos sueltos en SVG para el grupo (Canva los acepta como imagen y deja cambiarles el color)."""
    CARPETA_SVG.mkdir(exist_ok=True)
    for ico, d in trazos.items():
        (CARPETA_SVG / f'{ico}.svg').write_text(
            f'<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96" viewBox="0 0 24 24" fill="none" '
            f'stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="{d}"/></svg>\n',
            encoding='utf-8')


# ---------------------------------------------------------------- piezas del .pptx
def px(valor):
    return Emu(round(valor * EMU_POR_PX))


def rgb(color):
    return RGBColor.from_string(hex_de(color)[1:])


def agregar_reservado(lamina, caja, colores):
    """Recuadro punteado de «espacio reservado» como forma nativa, para que el grupo lo pueda borrar al llenarlo."""
    forma = lamina.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(caja['x']), px(caja['y']), px(caja['w']), px(caja['h']))
    forma.adjustments[0] = 12 / min(caja['w'], caja['h'])
    forma.fill.background()
    forma.line.color.rgb = rgb(colores['gris-base'])
    forma.line.width = px(3)
    forma.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    forma.shadow.inherit = False


def tramo(texto, familia, tam_px, color, peso=400):
    return {'t': texto, 'familia': familia, 'px': tam_px, 'peso': peso, 'color': color}


def caja_texto(contenedor, x, y, w, h, tramos, alin='left', interlineado=1.2, una_linea=True):
    caja = contenedor.add_textbox(px(x), px(y), px(w), px(h))
    marco = caja.text_frame
    marco.word_wrap = not una_linea
    marco.auto_size = None
    marco.vertical_anchor = MSO_ANCHOR.TOP
    marco.margin_left = marco.margin_right = marco.margin_top = marco.margin_bottom = 0
    parrafo = marco.paragraphs[0]
    parrafo.alignment = ALINEACION.get(alin, PP_ALIGN.LEFT)
    parrafo.line_spacing = 1.0 if una_linea else round(interlineado / INTERLINEADO_SIMPLE, 2)
    for t in tramos:
        run = parrafo.add_run()
        run.text = t['t']
        run.font.name = t['familia']
        run.font.size = Pt(t['px'] / 2)
        run.font.bold = t['peso'] >= 600
        run.font.italic = t.get('cursiva', False)
        run.font.color.rgb = rgb(t['color'])
    return caja


def agregar_bloque(lamina, bloque):
    x, w = bloque['x'], bloque['w']
    una_linea = bloque['lineas'] == 1
    ancho = w * HOLGURA_ANCHO + (12 if una_linea else 0)
    if bloque['alin'] == 'center':
        x -= (ancho - w) / 2
    elif bloque['alin'] in ('right', 'end'):
        x -= ancho - w
    caja_texto(lamina.shapes, x, bloque['y'], ancho, bloque['h'], bloque['runs'], bloque['alin'],
               bloque['interlineado'], una_linea)


def agregar_recorrido(lamina, n, tramo_actual, colores):
    """Línea de recorrido nativa y agrupada; el marcador «n / total» se puede mover y reescribir."""
    total, bloques = recorrido_del_deck()
    x0, ancho, y = 96, 1920 - 192, 1006
    x_parada = lambda k: x0 + (k - 1) / (total - 1) * ancho
    grupo = lamina.shapes.add_group_shape()
    g = grupo.shapes

    def linea(xa, xb, color):
        conector = g.add_connector(MSO_CONNECTOR.STRAIGHT, px(xa), px(y), px(xb), px(y))
        conector.line.color.rgb = rgb(color)
        conector.line.width = Pt(2)
    linea(x0, x0 + ancho, colores['linea'])
    linea(x0, x_parada(n), colores['rojo'])
    for k in range(1, total + 1):
        parada = g.add_shape(MSO_SHAPE.OVAL, px(x_parada(k) - 6), px(y - 6), px(12), px(12))
        parada.fill.solid()
        parada.fill.fore_color.rgb = rgb(colores['fondo'])
        parada.line.color.rgb = rgb(colores['rojo'] if k <= n else colores['linea'])
        parada.line.width = Pt(1.5)
    for i, (nombre, desde) in enumerate(bloques):
        hasta = (bloques[i + 1][1] if i + 1 < len(bloques) else total + 1) - 1
        centro = (x_parada(desde) + x_parada(hasta)) / 2
        actual = i == tramo_actual
        caja_texto(g, centro - 110, 1022, 220, 24,
                   [tramo(nombre, DISPLAY, 17, colores['texto'] if actual else colores['texto-2'], 600 if actual else 400)],
                   'center')
    etiqueta = f'{n} / {total}'
    ancho_marcador = 24 + 11 * len(etiqueta)
    marcador = g.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(x_parada(n) - ancho_marcador / 2), px(y - 16),
                           px(ancho_marcador), px(32))
    marcador.adjustments[0] = 0.5
    marcador.fill.solid()
    marcador.fill.fore_color.rgb = rgb(colores['rojo'])
    marcador.line.fill.background()
    marco = marcador.text_frame
    marco.margin_left = marco.margin_right = marco.margin_top = marco.margin_bottom = 0
    marco.vertical_anchor = MSO_ANCHOR.MIDDLE
    marco.word_wrap = False
    parrafo = marco.paragraphs[0]
    parrafo.alignment = PP_ALIGN.CENTER
    run = parrafo.add_run()
    run.text = etiqueta
    run.font.name, run.font.size, run.font.bold = DISPLAY, Pt(9), True
    run.font.color.rgb = rgb(colores['blanco'])
    return grupo


def fondo_liso(lamina, presentacion, color):
    rect = lamina.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, presentacion.slide_width, presentacion.slide_height)
    rect.fill.solid()
    rect.fill.fore_color.rgb = rgb(color)
    rect.line.fill.background()
    return rect


# ---------------------------------------------------------------- páginas de kit para el grupo
def cifras_ejemplo():
    """Buses del caso base y del plan de cuartetos (promedio de 3 semillas a 40 min), desde los resultados."""
    with open(AQUI.parent / 'kpi/resultados/kpi_planes.csv', encoding='utf-8-sig') as f:
        base = next(float(fila['caso_base_L']) for fila in csv.DictReader(f) if fila['kpi'] == 'buses')
    with open(AQUI.parent / 'octetos/resultados/red_completa_417_L.csv', encoding='utf-8-sig') as f:
        filas = [fila for fila in csv.DictReader(f) if fila['metodo'] == 'cuartetos' and fila['seleccion'] == 'azar'
                 and float(fila['presupuesto_s']) == 2400]
    return round(base), round(sum(float(fila['buses']) for fila in filas) / len(filas))


def pagina_kit(presentacion, vacia, colores, encabezado, titulo, frase, nota):
    lamina = presentacion.slides.add_slide(vacia)
    fondo_liso(lamina, presentacion, colores['fondo'])
    for bloque in encabezado:
        agregar_bloque(lamina, bloque)
    caja_texto(lamina.shapes, 96, 84, 1600, 72, [tramo(titulo, DISPLAY, 62, colores['texto'], 800)])
    caja_texto(lamina.shapes, 96, 168, 1600, 44, [tramo(frase, SERIF, 31, colores['texto-2'])])
    lamina.notes_slide.notes_text_frame.text = nota
    return lamina


def kit_estilo(lamina, colores):
    roles = [('rojo', 'RED y lo que se elimina: buses menos, ahorro'), ('azul', 'Nuestro plan'),
             ('gris-base', 'Caso base'), ('verde', 'Energía y recarga'), ('texto', 'Títulos y cifras'),
             ('texto-2', 'Frases y etiquetas'), ('fondo', 'Fondo de todas las láminas')]
    for i, (token, rol) in enumerate(roles):
        y = 260 + i * 78
        muestra = lamina.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, px(96), px(y), px(64), px(56))
        muestra.fill.solid()
        muestra.fill.fore_color.rgb = rgb(colores[token])
        muestra.line.color.rgb = rgb(colores['linea'])
        caja_texto(lamina.shapes, 184, y + 2, 520, 30, [tramo(colores[token], DISPLAY, 24, colores['texto'], 800)])
        caja_texto(lamina.shapes, 184, y + 32, 600, 28, [tramo(rol, SERIF, 21, colores['texto-2'])])
    escalas = [('Título de lámina', DISPLAY, 62, 800, 'Overpass Bold, 31 pt'),
               ('Frase corta debajo del título', SERIF, 31, 400, 'Source Serif 4, 15,5 pt'),
               ('Cifra grande', DISPLAY, 96, 800, 'Overpass Bold, de 36 a 125 pt'),
               ('Etiqueta o nota al pie', DISPLAY, 22, 400, 'Overpass, 11 pt')]
    y = 250
    for texto, familia, tam, peso, rotulo in escalas:
        caja_texto(lamina.shapes, 860, y, 960, tam * 1.15, [tramo(texto, familia, tam, colores['texto'], peso)])
        caja_texto(lamina.shapes, 860, y + tam * 1.15 + 4, 960, 26, [tramo(rotulo, DISPLAY, 18, colores['texto-2'])])
        y += tam * 1.15 + 48
    reglas = ('Una idea por lámina: una cifra grande y una frase corta; el detalle va en las notas. '
              'Cada cifra aparece una sola vez en el deck. Para un paso nuevo, dupliquen la página y agreguen lo nuevo. '
              'Muevan el marcador rojo de la línea de abajo y cambien su número.')
    caja_texto(lamina.shapes, 860, 800, 960, 140, [tramo(reglas, SERIF, 22, colores['texto-2'])],
               interlineado=1.4, una_linea=False)


def kit_iconos(lamina, colores, rutas_iconos, trazos):
    for i, ico in enumerate(sorted(trazos)):
        x, y = 96 + (i % 6) * 290, 250 + (i // 6) * 230
        for j, token in enumerate(('texto', 'azul', 'verde', 'rojo')):
            lamina.shapes.add_picture(str(rutas_iconos[(ico, colores[token])]), px(x + j * 60), px(y), px(52), px(52))
        caja_texto(lamina.shapes, x, y + 66, 260, 26, [tramo(ico, DISPLAY, 20, colores['texto-2'])])


def kit_grafico(lamina, colores):
    """Barras hechas con formas: se editan estirándolas. (El gráfico nativo de PowerPoint pierde los colores en Canva.)"""
    base, plan = cifras_ejemplo()
    x0, ancho_max, alto = 96, 1500, 120
    for i, (rotulo, valor, token) in enumerate((('Caso base', base, 'gris-base'), ('Nuestro plan', plan, 'azul'))):
        y = 290 + i * 190
        barra = lamina.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(x0), px(y + 36), px(ancho_max * valor / base), px(alto))
        barra.fill.solid()
        barra.fill.fore_color.rgb = rgb(colores[token])
        barra.line.fill.background()
        caja_texto(lamina.shapes, x0, y, 600, 30, [tramo(rotulo, DISPLAY, 24, colores['texto'], 600)])
        cifra = f'{valor:,}'.replace(',', '.')
        caja_texto(lamina.shapes, x0 + 28, y + 36 + 28, 600, 70, [tramo(f'{cifra} buses', DISPLAY, 56, colores['blanco'], 800)])
    caja_texto(lamina.shapes, x0, 720, 1500, 90,
               [tramo('Para un gráfico con datos nuevos: Elementos → Gráficos en Canva, y aplicar estos colores '
                      '(gris #888B8D para el caso base, azul #0D5DAB para nuestro plan, rojo #CF152D para lo que se elimina).',
                      SERIF, 24, colores['texto-2'])], interlineado=1.4, una_linea=False)


def kit(presentacion, vacia, colores, encabezado, rutas_iconos, trazos):
    aviso = 'Página de kit. No se presenta; bórrenla antes de exportar el PDF de entrega.'
    estilo = pagina_kit(presentacion, vacia, colores, encabezado, 'Kit del deck: guía de estilo',
                        'Esta página no se presenta: es la referencia para hacer láminas nuevas.', aviso)
    kit_estilo(estilo, colores)
    agregar_recorrido(estilo, 1, 0, colores)

    hoja = pagina_kit(presentacion, vacia, colores, encabezado, 'Kit del deck: íconos',
                      'Copien el que necesiten. También están en SVG en 09-entrega3/presentacion/iconos/.', aviso)
    kit_iconos(hoja, colores, rutas_iconos, trazos)

    plantilla = pagina_kit(presentacion, vacia, colores, encabezado, 'Título de la lámina, en una línea',
                           'Una frase corta que diga la idea de la lámina.',
                           'Plantilla: dupliquen esta página para cada lámina nueva y escriban el guion aquí '
                           '(2,3 palabras por segundo).')
    caja_texto(plantilla.shapes, 90, 300, 1200, 240, [tramo('Cifra', DISPLAY, 220, colores['texto'], 800)])
    caja_texto(plantilla.shapes, 96, 560, 900, 90,
               [tramo('qué mide la cifra y de dónde sale, en una o dos líneas', SERIF, 34, colores['texto-2'])],
               interlineado=1.3, una_linea=False)
    plantilla.shapes.add_picture(str(rutas_iconos[('bus', colores['texto'])]), px(1100), px(320), px(72), px(72))
    agregar_recorrido(plantilla, 12, 3, colores)

    grafico = pagina_kit(presentacion, vacia, colores, encabezado, 'Ejemplo de gráfico con los colores del deck',
                         'Barras hechas con formas: para cambiar un valor, estiren la barra y cambien la cifra.',
                         'Página de kit. Datos reales: buses del caso base y del plan de cuartetos (promedio de 3 semillas).')
    kit_grafico(grafico, colores)
    agregar_recorrido(grafico, 12, 3, colores)


# ---------------------------------------------------------------- armado
def lamina_inicial():
    """Con --desde N se exportan solo las láminas N en adelante, sin páginas de kit (para agregarlas a Canva)."""
    if '--desde' not in sys.argv:
        return 1
    i = sys.argv.index('--desde')
    if i + 1 >= len(sys.argv) or not sys.argv[i + 1].isdigit():
        raise SystemExit('Uso: exportar_pptx.py [--desde N]')
    return int(sys.argv[i + 1])


def main():
    TRABAJO.mkdir(exist_ok=True)
    desde = lamina_inicial()
    salida = SALIDA if desde == 1 else SALIDA.with_name(f'{SALIDA.stem}_desde{desde}.pptx')
    colores = tokens()
    trazos = iconos_del_deck()
    trabajo = [(n, p) for n, pasos in paginas() if n >= desde for p in range(pasos)]
    print(f'{len(trabajo)} páginas a capturar', flush=True)
    with ThreadPoolExecutor(max_workers=3) as grupo:
        capturas = list(grupo.map(lambda np: capturar(*np), trabajo))

    combinaciones = {(i['ico'], hex_de(i['color'])) for _, m in capturas for i in m['iconos']}
    combinaciones |= {(ico, colores[t]) for ico in trazos for t in ('texto', 'azul', 'verde', 'rojo')}
    rutas_iconos = rasterizar_iconos(combinaciones, trazos)
    guardar_svg(trazos, colores['texto'])

    presentacion = Presentation()
    presentacion.slide_width, presentacion.slide_height = Emu(1920 * EMU_POR_PX), Emu(1080 * EMU_POR_PX)
    vacia = presentacion.slide_layouts[6]
    encabezado = []
    for png, medidas in capturas:
        lamina = presentacion.slides.add_slide(vacia)
        lamina.shapes.add_picture(str(png), 0, 0, presentacion.slide_width, presentacion.slide_height)
        for caja in medidas.get('reservados', []):
            agregar_reservado(lamina, caja, colores)
        for icono in medidas['iconos']:
            ruta = rutas_iconos[(icono['ico'], hex_de(icono['color']))]
            lamina.shapes.add_picture(str(ruta), px(icono['x']), px(icono['y']), px(icono['w']), px(icono['h']))
        for bloque in medidas['bloques']:
            agregar_bloque(lamina, bloque)
        if medidas['n'] > 1 and not medidas.get('anexo'):
            agregar_recorrido(lamina, medidas['n'], medidas['tramo'], colores)
            if not encabezado:
                encabezado = [b for b in medidas['bloques'] if b['y'] < 70]
        paso = f' (paso {medidas["paso"] + 1} de {medidas["pasos"]})' if medidas['pasos'] > 1 else ''
        nombre = f'Anexo {medidas["anexo"]}' if medidas.get('anexo') else f'Lámina {medidas["n"]}'
        lamina.notes_slide.notes_text_frame.text = f'{nombre}{paso}. {medidas["notas"]}'
    if desde == 1 and '--sin-kit' not in sys.argv:
        kit(presentacion, vacia, colores, encabezado, rutas_iconos, trazos)
    presentacion.save(salida)
    print(f'{len(presentacion.slides)} páginas ({len(capturas)} del deck) en {salida.name} '
          f'({salida.stat().st_size / 1e6:.1f} MB); {len(rutas_iconos)} íconos PNG; SVG en {CARPETA_SVG.name}/')


if __name__ == '__main__':
    sys.exit(main())
