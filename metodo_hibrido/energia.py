"""Batería y reserva de los buses (kWh) y consumo (kWh/km).

Por omisión son 350 y 35 kWh y 1,4 kWh/km (el caso del enunciado). Para los casos con recarga forzada se cambian
con las variables de entorno BATERIA_KWH y RESERVA_KWH, y en la sensibilidad
el consumo con CONSUMO_KWH_KM; load_instance rechaza un caso cuyo
escenario.json declare otros valores, así que un caso no se puede correr con la batería equivocada.
"""
import os

def _leer(nombre, omision):
    valor = float(os.environ.get(nombre, omision))
    if valor <= 0:
        raise ValueError(f'{nombre} debe ser positivo: {valor}')
    return valor


BATERIA = _leer('BATERIA_KWH', 350.)
RESERVA = _leer('RESERVA_KWH', 35.)
CONSUMO = _leer('CONSUMO_KWH_KM', 1.4)
if RESERVA >= BATERIA:
    raise ValueError(f'La reserva ({RESERVA}) debe ser menor que la batería ({BATERIA})')
