"""Genera el guion de la presentación final en LaTeX (para Overleaf) a partir de guion.html.

guion.html es la única fuente: sus constantes BLOQUES, LAMINAS, PREGUNTAS y REGLAS se leen con Node.
Uso, desde la raíz del repositorio:
    python3 09-entrega3/presentacion/guion_tex.py
Escribe 09-entrega3/presentacion/guion_latex/guion.tex (compila con pdflatex en Overleaf o en local).
"""
import json
import re
import subprocess
from pathlib import Path

CARPETA = Path(__file__).resolve().parent
FUENTE = CARPETA / 'guion.html'
SALIDA = CARPETA / 'guion_latex' / 'guion.tex'
PALABRAS_POR_SEGUNDO = 2.3
ULTIMA_LAMINA = 21

EXTRAER = r"""
const fs = require('fs');
const html = fs.readFileSync(process.argv[1], 'utf8');
const ini = html.indexOf('const BLOQUES'), fin = html.indexOf('const PALABRAS_POR_SEGUNDO');
if (ini < 0 || fin < 0) { console.error('No encontré los datos del guion en guion.html'); process.exit(1); }
const datos = new Function(html.slice(ini, fin) + '; return {BLOQUES, LAMINAS, PREGUNTAS, REGLAS};')();
process.stdout.write(JSON.stringify(datos));
"""


def leer_datos(fuente):
    """Lee las constantes del guion desde el HTML ejecutando solo ese tramo del script con Node."""
    resultado = subprocess.run(['node', '-e', EXTRAER, str(fuente)], capture_output=True, text=True, check=False)
    if resultado.returncode != 0:
        raise SystemExit(f'No se pudieron leer los datos de {fuente}: {resultado.stderr.strip()}')
    return json.loads(resultado.stdout)


ESPECIALES = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
              '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}', '→': r'\textrightarrow{}'}


def escapar(texto):
    return ''.join(ESPECIALES.get(c, c) for c in texto)


def texto_plano(voz):
    return re.sub(r'\[\[pausa\]\]', '', re.sub(r'\[\[traspaso:([^\]]*)\]\]', r'\1', voz))


def palabras(voz):
    return len(texto_plano(voz).split())


def marcar(voz):
    """Escapa el texto y convierte las marcas del guion en comandos LaTeX."""
    salida = []
    for parte in re.split(r'(\[\[traspaso:[^\]]*\]\]|\[\[pausa\]\])', voz):
        traspaso = re.fullmatch(r'\[\[traspaso:([^\]]*)\]\]', parte)
        if traspaso:
            salida.append(r'\traspaso{' + escapar(traspaso.group(1)) + '}')
        elif parte == '[[pausa]]':
            salida.append(r'\pausa{}')
        else:
            salida.append(escapar(parte))
    return ''.join(salida)


def reloj(segundos):
    total = round(segundos)
    return f'{total // 60}:{total % 60:02d}'


def paginas(primera, ultima):
    return f'pág.~{primera}' if primera == ultima else f'págs.~{primera}--{ultima}'


def resumen_bloque(bloque, laminas):
    propias = [l for l in laminas if bloque['desde'] <= l['n'] <= bloque['hasta']]
    total = sum(palabras(v) for l in propias for v in l['voz'])
    clics = sum(l['p'][1] - l['p'][0] + (1 if l['n'] < ULTIMA_LAMINA else 0) for l in propias)
    return propias, total, clics


def ficha(lamina, siguiente):
    lineas = [rf"\lamina{{{lamina['n']}}}{{{escapar(lamina['t'])}}}{{{paginas(*lamina['p'])}}}{{{lamina['s']}~s}}"]
    for i, voz in enumerate(lamina['voz']):
        clic = rf" \clic{{{lamina['p'][0] + i + 1}}}" if i < len(lamina['voz']) - 1 else ''
        lineas.append(marcar(voz) + clic + '\n')
    if siguiente is not None:
        lineas.append(rf"\siguiente{{{siguiente['n']}}}{{{siguiente['p'][0]}}}" + '\n')
    elif lamina.get('fin'):
        lineas.append(rf"\fcolorbox{{linea}}{{white}}{{\sffamily\scriptsize\bfseries\color{{gris}}{escapar(lamina['fin'].upper())}}}" + '\n')
    for pregunta, respuesta in lamina.get('si', []):
        lineas.append(rf"\begin{{sipreguntan}}{{{escapar(pregunta)}}}{escapar(respuesta)}\end{{sipreguntan}}")
    return '\n'.join(lineas)


def seccion_bloque(clave, bloque, laminas, reglas):
    propias, total, clics = resumen_bloque(bloque, laminas)
    primera, ultima = propias[0]['p'][0], propias[-1]['p'][1]
    fichas = []
    for lam in propias:
        siguiente = next((x for x in laminas if x['n'] == lam['n'] + 1 and x['n'] <= ULTIMA_LAMINA), None)
        fichas.append(ficha(lam, siguiente))
    reglas_tex = '\n'.join(rf'  \item {escapar(r)}' for r in reglas)
    return rf"""
\clearpage
\section{{{escapar(bloque['nombre'])}}}\label{{{clave}}}
\begin{{resumen}}
Láminas {bloque['desde']}--{bloque['hasta']} \quad·\quad Canva {paginas(primera, ultima)} \quad·\quad
Tiempo {reloj(total / PALABRAS_POR_SEGUNDO)} ({total} palabras a 2,3 por segundo) \quad·\quad {clics} clics\\
{escapar(bloque['entra'])} {escapar(bloque['sale'])}
\end{{resumen}}
\begin{{reglas}}{{Antes de empezar}}
\begin{{itemize}}[leftmargin=*, itemsep=1pt]
{reglas_tex}
\end{{itemize}}
\end{{reglas}}

{chr(10).join(fichas)}
"""


def portada(bloques, laminas):
    filas = []
    total_general = 0
    for bloque in bloques.values():
        propias, total, clics = resumen_bloque(bloque, laminas)
        total_general += total
        filas.append(rf"{escapar(bloque['nombre'])} & {bloque['desde']}--{bloque['hasta']} & "
                     rf"{propias[0]['p'][0]}--{propias[-1]['p'][1]} & {reloj(total / PALABRAS_POR_SEGUNDO)} & {clics} \\")
    tabla = '\n'.join(filas)
    return rf"""
{{\sffamily\small\color{{gris}}\textbf{{\color{{rojo}}ICS2122}} · Capstone · Grupo 29 · Entrega final}}

\vspace{{4pt}}
{{\sffamily\bfseries\Huge Guion de la presentación final}}

\vspace{{8pt}}
Lo que dice cada expositor, palabra por palabra, y en qué página de Canva debe estar en cada momento.
Cada clic avanza una página. Meta: 14 minutos en total, sin hablar más rápido.

\vspace{{10pt}}
\begin{{tabular}}{{@{{}}l c c c c@{{}}}}
\toprule
\textbf{{Expositor}} & \textbf{{Láminas}} & \textbf{{Págs. de Canva}} & \textbf{{Tiempo}} & \textbf{{Clics}} \\
\midrule
{tabla}
\midrule
\textbf{{Total}} & 1--{ULTIMA_LAMINA} & & \textbf{{{reloj(total_general / PALABRAS_POR_SEGUNDO)}}} & \\
\bottomrule
\end{{tabular}}

\vspace{{8pt}}
{{\small\color{{gris}}Tiempos medidos a 2,3 palabras por segundo. \clic{{n}} indica la página que debe aparecer
al hacer clic; \traspaso{{texto}} es la frase que pasa la palabra; \pausa{{}} es un silencio de un segundo.}}
"""


def seccion_preguntas(preguntas):
    filas = '\n'.join(rf"\textbf{{{escapar(p)}}} & {escapar(q)} & {escapar(r)} & {{\small {escapar(ir)}}} \\ \midrule"
                      for p, q, r, ir in preguntas)
    return rf"""
\clearpage
\section{{Preguntas}}\label{{preguntas}}
\begin{{reglas}}{{Cómo responder}}
\begin{{itemize}}[leftmargin=*, itemsep=1pt]
  \item Responde quien figura en la columna «Responde». Si necesita una lámina o un anexo, lo pide y quien tenga el control salta a esa página.
  \item Respuestas de una o dos frases. Si quieren más detalle, se muestra el anexo.
  \item En el modo presentación de Canva se salta a una página escribiendo su número y Enter.
\end{{itemize}}
\end{{reglas}}

{{\small
\begin{{longtable}}{{@{{}}>{{\raggedright\arraybackslash}}p{{3.5cm}} >{{\raggedright\arraybackslash}}p{{1.95cm}} >{{\raggedright\arraybackslash}}p{{7.45cm}} >{{\raggedright\arraybackslash}}p{{2.5cm}}@{{}}}}
\toprule
\textbf{{Pregunta}} & \textbf{{Responde}} & \textbf{{Respuesta corta}} & \textbf{{Mostrar}} \\ \midrule
\endhead
{filas}
\end{{longtable}}}}
"""


PREAMBULO = r"""\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-noshorthands,es-nodecimaldot]{babel}
\usepackage{lmodern}
\usepackage[a4paper,margin=2cm]{geometry}
\usepackage{xcolor}
\usepackage{booktabs,longtable,array}
\usepackage{enumitem}
\usepackage[breakable,skins]{tcolorbox}
\usepackage{setspace}
\usepackage[hidelinks]{hyperref}

% Colores de RED, los mismos del deck
\definecolor{rojo}{HTML}{CF152D}
\definecolor{azul}{HTML}{0D5DAB}
\definecolor{azulsuave}{HTML}{E3ECF6}
\definecolor{gris}{HTML}{58595B}
\definecolor{linea}{HTML}{D5D7D8}

\setlength{\parindent}{0pt}
\setlength{\parskip}{3pt}
\setlength{\emergencystretch}{2em}
\pagestyle{plain}

\newcommand{\clic}[1]{\hspace{2pt}\colorbox{azulsuave}{\sffamily\scriptsize\bfseries\color{azul}CLIC \textrightarrow{} PÁG.~#1}}
\newcommand{\siguiente}[2]{\fcolorbox{linea}{white}{\sffamily\scriptsize\bfseries\color{gris}CLIC \textrightarrow{} LÁMINA #1, PÁG.~#2}}
\newcommand{\traspaso}[1]{{\color{rojo}\sffamily\scriptsize\bfseries TRASPASO · }{\color{rojo}\bfseries #1}}
\newcommand{\pausa}{{\color{rojo}\sffamily\scriptsize\bfseries (PAUSA DE UN SEGUNDO)}}
\newcommand{\lamina}[4]{\par\vspace{10pt}\noindent\rule{\linewidth}{0.4pt}\par\nopagebreak\vspace{4pt}%
  \noindent{\sffamily\bfseries\LARGE #1}\hspace{10pt}{\sffamily\bfseries\large #2}\hfill{\sffamily\small\color{gris}#3 · #4}%
  \par\nopagebreak\vspace{4pt}\setstretch{1.25}}
\newtcolorbox{sipreguntan}[1]{enhanced, breakable, colback=white, colframe=linea, boxrule=0.5pt, arc=2pt,
  left=6pt, right=6pt, top=4pt, bottom=4pt, fontupper=\small\setstretch{1.05},
  before upper={{\sffamily\scriptsize\bfseries\color{gris}SI PREGUNTAN: \MakeUppercase{#1}}\par}}
\newtcolorbox{reglas}[1]{enhanced, breakable, colback=white, colframe=linea, boxrule=0.5pt, arc=2pt,
  left=8pt, right=8pt, top=4pt, bottom=4pt, fontupper=\small,
  before upper={{\sffamily\scriptsize\bfseries\color{gris}\MakeUppercase{#1}}\par}}
\newenvironment{resumen}{\par\sffamily\small\color{gris}}{\par\vspace{4pt}}

\makeatletter
\renewcommand\section{\@startsection{section}{1}{0pt}{-6pt}{8pt}{\sffamily\bfseries\Huge}}
\makeatother
\setcounter{secnumdepth}{0}
"""


def main():
    datos = leer_datos(FUENTE)
    bloques, laminas = datos['BLOQUES'], datos['LAMINAS']
    cuerpo = [portada(bloques, laminas)]
    cuerpo += [seccion_bloque(clave, bloque, laminas, datos['REGLAS']) for clave, bloque in bloques.items()]
    cuerpo.append(seccion_preguntas(datos['PREGUNTAS']))
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(PREAMBULO + '\\begin{document}\n' + '\n'.join(cuerpo) + '\n\\end{document}\n', encoding='utf-8')
    print(f'Escrito {SALIDA.relative_to(CARPETA.parent.parent)}')


if __name__ == '__main__':
    main()
