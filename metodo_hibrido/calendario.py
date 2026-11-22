"""Heurística constructiva con calendario compartido; no prueba optimalidad."""
import math
import numpy as np

BLOQUE, MAX_CARGA = 300, 15.
EPS = 1e-7

def precio(second, tariffs):
    hour = (second % 86400)/3600
    return next(p for a, b, p in tariffs if a <= hour < b)

class Calendario:
    """Ocupación física a segundo entero y conexiones por bloque de cinco minutos."""
    def __init__(self, physical, plugs, t0, horizon):
        self.physical, self.plugs = physical, plugs
        self.t0, self.horizon = t0, horizon
        self.presence = {e: np.zeros(horizon-t0, dtype=np.int32) for e in physical}
        self.connections = {e: {} for e in physical}

    def libre(self, e, start, end, charging=False):
        if start < self.t0 or end > self.horizon or end < start:
            return False
        if end > start and np.max(self.presence[e][start-self.t0:end-self.t0]) >= self.physical[e]:
            return False
        if charging:
            return all(self.connections[e].get(t, 0) < self.plugs[e] for t in range(start, end, BLOQUE))
        return True

    def reservar(self, e, start, end, charging=False):
        if not self.libre(e, start, end, charging):
            raise AssertionError('Reserva que excede capacidad')
        self.presence[e][start-self.t0:end-self.t0] += 1
        if charging:
            for t in range(start, end, BLOQUE):
                self.connections[e][t] = self.connections[e].get(t, 0)+1

def actividad(kind, origin, target, start, end, km=0., q=0., trip=''):
    return dict(tipo=kind, origen=origin, destino=target, inicio_s=int(start), fin_s=int(end),
                distancia_km=float(km), carga_kwh=float(q), corrida_id=trip)

def agregar_viaje(result, origin, target, start, distances):
    km, duration = distances[origin, target]
    if duration or km:
        result.append(actividad('vacio', origin, target, start, start+duration, km))
    return start+duration

def esperar(result, loc, start, end):
    if end > start:
        result.append(actividad('espera', loc, loc, start, end))
