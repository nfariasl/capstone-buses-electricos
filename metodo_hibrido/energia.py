"""Batería y reserva de los buses, en kWh.

Por omisión son 350 y 35 kWh (el caso del enunciado). Para los casos con recarga forzada se cambian
con las variables de entorno BATERIA_KWH y RESERVA_KWH; load_instance rechaza un caso cuyo
escenario.json declare otros valores, así que un caso no se puede correr con la batería equivocada.
"""
import os

CONSUMO = 1.4


def _leer(nombre, omision):
    valor = float(os.environ.get(nombre, omision))
    if valor <= 0:
        raise ValueError(f'{nombre} debe ser positivo: {valor}')
    return valor


BATERIA = _leer('BATERIA_KWH', 350.)
RESERVA = _leer('RESERVA_KWH', 35.)
if RESERVA >= BATERIA:
    raise ValueError(f'La reserva ({RESERVA}) debe ser menor que la batería ({BATERIA})')
