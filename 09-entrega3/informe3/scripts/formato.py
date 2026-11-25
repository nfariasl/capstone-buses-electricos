"""Números en formato chileno y macros LaTeX para cifras.tex."""
import math
import re

NOMBRE_MACRO = re.compile(r'^[A-Za-z]+$')


def numero(valor, decimales=0):
    if not math.isfinite(valor):
        raise ValueError(f'Cifra no finita: {valor}')
    redondeado = round(valor, decimales)
    if redondeado == 0:
        redondeado = 0.0
    texto = f'{redondeado:,.{decimales}f}'
    return texto.replace(',', '_').replace('.', ',').replace('_', '.')


def con_signo(valor, decimales=0):
    texto = numero(abs(valor), decimales)
    if round(valor, decimales) == 0:
        return texto
    return ('+' if valor > 0 else '\\ensuremath{-}') + texto


def delta(base, nuevo):
    if base == 0:
        raise ValueError('No se puede calcular un cambio porcentual con base cero')
    diferencia = nuevo - base
    return diferencia, 100 * diferencia / base


def macro(nombre, valor):
    if not NOMBRE_MACRO.match(nombre):
        raise ValueError(f'Nombre de macro inválido (solo letras): {nombre}')
    return f'\\newcommand{{\\{nombre}}}{{{valor}}}'
