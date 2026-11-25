"""Revisa el .tex y el PDF del informe final: cifras a mano, vocabulario, dos puntos, negritas y páginas."""
import re
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parents[1]
LIMITE_PAGINAS = 45
PRESUPUESTO = {1: 2, 2: 4, 3: 5, 4: 4, 5: 5, 6: 5, 7: 3, 8: 10, 9: 8, 10: 3, 11: 2}
# Preferencia de la usuaria: nada de dos puntos en la prosa ni negritas.
DOS_PUNTOS = re.compile(r'[^\s\\{}\[\]0-9]: ')
NEGRITA = re.compile(r'\\textbf\{')
RESTOS_PLANTILLA = ('First Appendix', 'Short Story', 'selfie_monkey', 'Miembro 1',
                    'NOMBRE PROYECTO', 'GRUPO XX', 'Chapter 1', 'Lorem')
NUMERO_A_MANO = re.compile(r'(?<![\w\\.,{])(?:\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+,\d+)(?![\w])')
PALABRA_PROHIBIDA = re.compile(r'(?<!tiempos de )(?<!tiempo de )\bviajes?\b', re.IGNORECASE)
COMENTARIO = re.compile(r'(?<!\\)%.*$')
MARCA_LITERAL = '%literal'
PENDIENTE = re.compile(r'\\nocite\{\*\}|\[POR COMPLETAR[^\]]*\]')
ENTRADA_TOC = re.compile(r'^\\contentsline\s*\{chapter\}\{(?P<titulo>.*)\}'
                         r'\{(?P<pagina>[^{}]*)\}\{[^{}]*\}%?\s*$')
# pucthesis escribe \tocchapter {}{N}{TÍTULO}; las clases estándar, \numberline {N}
CAPITULO = re.compile(r'\\numberline\s*\{(?P<n>\d+)\.?\}|\\tocchapter\s*\{[^{}]*\}\{(?P<m>\d+)\}')
ROTULOS_INGLES = (re.compile(r'\bAPPENDIX\b'), re.compile(r'\bFigure \d'),
                  re.compile(r'\bTable \d'), re.compile(r'TABLE OF CONTENTS|LIST OF'))


def problemas_en_tex(nombre, texto):
    errores, pendientes = [], []
    en_tikz = False
    for numero, linea in enumerate(texto.splitlines(), start=1):
        lugar = f'{nombre}:{numero}'
        if '\\begin{tikzpicture}' in linea:
            en_tikz = True
        for marca in PENDIENTE.finditer(linea):
            pendientes.append(f'{lugar}: pendiente «{marca.group(0)}»')
        codigo = '' if linea.rstrip().endswith(MARCA_LITERAL) else COMENTARIO.sub('', linea)
        if not en_tikz:
            for cifra in NUMERO_A_MANO.findall(codigo):
                errores.append(f'{lugar}: cifra escrita a mano «{cifra}»; usar una macro de cifras.tex')
        if not en_tikz and DOS_PUNTOS.search(codigo):
            errores.append(f'{lugar}: dos puntos en la prosa')
        if NEGRITA.search(codigo) and nombre != 'informe3.tex':
            errores.append(f'{lugar}: negrita')
        if PALABRA_PROHIBIDA.search(codigo):
            errores.append(f'{lugar}: usar «corrida», no «viaje»')
        for resto in RESTOS_PLANTILLA:
            if resto in codigo:
                errores.append(f'{lugar}: resto de la plantilla «{resto}»')
        if '\\end{tikzpicture}' in linea:
            en_tikz = False
    return errores, pendientes


def problemas_en_pdf(texto):
    problemas = []
    if '??' in texto:
        problemas.append('PDF: hay referencias o citas sin resolver («??»)')
    for patron in ROTULOS_INGLES:
        if patron.search(texto):
            problemas.append(f'PDF: rótulo en inglés «{patron.search(texto).group(0)}»')
    return problemas


def paginas_por_capitulo(toc):
    inicios, referencias = [], None
    for linea in toc.splitlines():
        entrada = ENTRADA_TOC.match(linea.strip())
        if not entrada or not entrada['pagina'].isdigit():
            continue
        capitulo = CAPITULO.search(entrada['titulo'])
        if capitulo:
            inicios.append((int(capitulo['n'] or capitulo['m']), int(entrada['pagina'])))
        elif 'REFERENCIAS' in entrada['titulo']:
            referencias = int(entrada['pagina'])
    if referencias is None or not inicios:
        raise ValueError('El índice no tiene capítulos numerados o falta REFERENCIAS')
    finales = [inicio for _, inicio in inicios[1:]] + [referencias]
    capitulos = {n: fin - inicio for (n, inicio), fin in zip(inicios, finales)}
    return {'capitulos': capitulos, 'total': referencias - inicios[0][1]}


def main(final=False):
    errores, pendientes, alertas = [], [], []
    archivos = [AQUI / 'informe3.tex'] + sorted((AQUI / 'chapters').glob('*.tex'))
    for archivo in archivos:
        e, p = problemas_en_tex(archivo.name, archivo.read_text(encoding='utf-8'))
        errores += e
        pendientes += p
    texto_pdf = subprocess.run(['pdftotext', str(AQUI / 'informe3.pdf'), '-'],
                               capture_output=True, text=True, check=True).stdout
    errores += problemas_en_pdf(texto_pdf)
    paginas = paginas_por_capitulo((AQUI / 'informe3.toc').read_text(encoding='utf-8', errors='replace'))
    if paginas['total'] > LIMITE_PAGINAS:
        errores.append(f'Páginas: {paginas["total"]} > {LIMITE_PAGINAS}')
    for n, usadas in paginas['capitulos'].items():
        if usadas > PRESUPUESTO[n]:
            alertas.append(f'Capítulo {n}: {usadas} págs. (presupuesto {PRESUPUESTO[n]})')
    print(f'Páginas del cuerpo: {paginas["total"]} / {LIMITE_PAGINAS} · por capítulo: {paginas["capitulos"]}')
    for grupo, lineas in (('ERROR', errores), ('PENDIENTE', pendientes), ('ALERTA', alertas)):
        for linea in lineas:
            print(f'{grupo} {linea}')
    return 1 if errores or (final and pendientes) else 0


if __name__ == '__main__':
    sys.exit(main(final='--final' in sys.argv))
