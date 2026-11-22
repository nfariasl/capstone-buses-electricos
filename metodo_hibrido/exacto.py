"""Respuesta perfecta para casos chicos: un solo MILP decide qué bus hace cada servicio y cuándo recarga.

Usa el mismo costo que el revisor y el mismo catálogo de recargas que la mejora por grupos
(recarga.opciones con interior=True), así que su óptimo es la regla para medir a los demás métodos.
Cada jornada parte del terminal de espera más cercano (no tienen límite de capacidad, así que es
óptimo) y el modelo elige dónde termina, respetando las plazas de los electroterminales.

Con podar=True (casos medianos) el modelo cabe en un computador de 8 GB: de cada par de servicios se
dejan solo las recargas no dominadas y no se escriben las restricciones de capacidad. Una recarga A
domina a B si va y vuelve con menos o iguales km, puede cargar al menos lo mismo y es igual o más
barata por kWh; cualquier plan que use B se cambia por A cargando menos y queda igual de factible y
no más caro. Así el modelo podado sin capacidades es una relajación con el mismo óptimo que el
modelo completo sin capacidades: su cota inferior vale para el modelo completo y, si su plan pasa
el revisor (que sí revisa conexiones y plazas), ese plan es óptimo también para el modelo completo.
"""
from collections import defaultdict
import gurobipy as gp
from metodo_hibrido.calendario import Calendario
from metodo_hibrido.conjunta import armar_plan
from metodo_hibrido.recarga import opciones
from metodo_hibrido.energia import BATERIA as _BATERIA, CONSUMO, RESERVA as _RESERVA

COSTO_BUS, COSTO_KM, COSTO_SESION = 250, .5, 5
BLOQUE = 300
# Margen numérico: con indicadores, Gurobi acepta violaciones de ~1e-4 kWh, que el revisor rechaza
# (pasó con 4 hilos: 34,9999 kWh contra una reserva de 35). El modelo usa una batería un poco más estrecha.
MARGEN_KWH = 1e-3
BATERIA, RESERVA = _BATERIA - MARGEN_KWH, _RESERVA + MARGEN_KWH


def _extremos(trip, d, starts, calendar):
    """(km, terminal) del inicio más cercano y la lista de finales que alcanzan a tiempo."""
    first, last = 'S:' + trip['inicio_stop_id'], 'S:' + trip['fin_stop_id']
    inicios = [(d[t, first][0], t) for t in starts
               if d.get((t, first)) is not None and calendar.t0 + d[t, first][1] <= trip['inicio_s']]
    finales = [(d[last, t][0], t) for t in starts + sorted(calendar.physical)
               if d.get((last, t)) is not None and trip['fin_s'] + d[last, t][1] <= calendar.horizon]
    if not inicios or not finales:
        raise ValueError(f"Servicio sin terminal alcanzable: {trip['corrida_id']}")
    return min(inicios), sorted(finales)


def _no_dominadas(lista):
    """Frontera de Pareto en (km1, km2, -maxq, price): menos km, más carga posible, más barata."""
    lista = sorted(lista, key=lambda c: (c['km1'] + c['km2'], -c['maxq'], c['price'], c['km1']))
    frontera = []
    for c in lista:
        if not any(f['km1'] <= c['km1'] and f['km2'] <= c['km2'] and f['maxq'] >= c['maxq']
                   and f['price'] <= c['price'] for f in frontera):
            frontera.append(c)
    return frontera


def _podar(lista):
    """Primero, dentro de cada electroterminal (mismos km), la más barata para cada carga máxima."""
    mejor = {}
    for c in lista:
        clave = c['e'], c['maxq']
        if clave not in mejor or c['price'] < mejor[clave]['price']:
            mejor[clave] = c
    return _no_dominadas(mejor.values())


def _enlaces(trips, d, calendar, tariffs, podar=False):
    """Encadenamientos directos (i, j, km) y con recarga (i, j, opción) dentro de cada sector."""
    directos, recargas = [], []
    for i, a in enumerate(trips):
        end = 'S:' + a['fin_stop_id']
        for j, b in enumerate(trips):
            if i == j or a['sector_id'] != b['sector_id'] or b['inicio_s'] < a['fin_s']:
                continue
            start = 'S:' + b['inicio_stop_id']
            directo = d.get((end, start))
            if directo is not None and a['fin_s'] + directo[1] <= b['inicio_s']:
                directos.append((i, j, directo[0]))
            if all(d.get((end, e)) is not None and d.get((e, start)) is not None for e in calendar.physical):
                lista = opciones(end, start, a['fin_s'], b['inicio_s'], d, calendar, tariffs, interior=True)
                recargas += [(i, j, c) for c in (_podar(lista) if podar else lista)]
    return directos, recargas


def _capacidades(model, recargas, y, llegadas, physical, plugs):
    """Conexiones y plazas por bloque; solo donde la demanda posible supera la capacidad."""
    cargando = defaultdict(list)
    for a, (_, _, c) in enumerate(recargas):
        for s in range(c['start'], c['end'], BLOQUE):
            cargando[c['e'], s].append(y[a])
    restricciones = 0
    for (e, s), ys in cargando.items():
        if len(ys) > plugs[e]:
            model.addConstr(gp.quicksum(ys) <= plugs[e])
            restricciones += 1
        estacionados = [v for llegada, v in llegadas[e] if llegada < s + BLOQUE]
        if len(ys) + len(estacionados) > physical[e]:
            model.addConstr(gp.quicksum(ys) + gp.quicksum(estacionados) <= physical[e])
            restricciones += 1
    for e, lista in llegadas.items():
        if len(lista) > physical[e]:
            model.addConstr(gp.quicksum(v for _, v in lista) <= physical[e])
            restricciones += 1
    return restricciones


def _jornadas(trips, ext, directos, recargas, u, v, x, y, q, calendar, d):
    siguiente = {}
    for a, (i, j, _) in enumerate(directos):
        if x[a].X > .5:
            siguiente[i] = (j, None)
    for a, (i, j, c) in enumerate(recargas):
        if y[a].X > .5:
            siguiente[i] = (j, (c, q[a].X))
    plans = []
    for primero in sorted(j for j in range(len(trips)) if u[j].X > .5):
        cadena, cargas = [primero], {}
        while cadena[-1] in siguiente:
            nxt, carga = siguiente[cadena[-1]]
            if carga:
                cargas[len(cadena)] = carga
            cadena.append(nxt)
        final = next(f for _, f in ext[cadena[-1]][1] if v[cadena[-1], f].X > .5)
        plan = armar_plan([trips[k] for k in cadena], ext[primero][0][1], final, cargas,
                          'respuesta_perfecta', calendar, d)
        plan['bus_id'] = str(len(plans))
        plans.append(plan)
    return plans


def resolver_exacto(trips, d, starts, physical, plugs, tariffs, t0, horizon, limit=600., gap=0., hilos=1,
                    podar=False):
    """Devuelve (planes o None, info). info['optimo'] dice si Gurobi demostró el óptimo.

    info['cota_usd'] es la cota inferior de Gurobi, también cuando no alcanzó a encontrar un plan.
    """
    calendar = Calendario(physical, plugs, t0, horizon)
    n = len(trips)
    ext = [_extremos(t, d, starts, calendar) for t in trips]
    directos, recargas = _enlaces(trips, d, calendar, tariffs, podar)
    model = gp.Model('respuesta_perfecta')
    model.Params.OutputFlag = 0
    model.Params.Threads = hilos
    model.Params.TimeLimit = limit
    model.Params.MIPGap = gap
    model.Params.FeasibilityTol = 1e-8
    if podar:
        model.Params.NodefileStart = 1.  # el árbol pasa a disco sobre 1 GB, para no agotar la memoria
    try:
        u = model.addVars(n, vtype='B', name='inicio')
        v = model.addVars([(j, f) for j in range(n) for _, f in ext[j][1]], vtype='B', name='final')
        e = model.addVars(n, lb=RESERVA, ub=BATERIA, name='energia')
        x = model.addVars(len(directos), vtype='B', name='directo')
        y = model.addVars(len(recargas), vtype='B', name='recarga')
        q = model.addVars(len(recargas), lb=0, name='kwh')
        entra, sale = defaultdict(list), defaultdict(list)
        for a, (i, j, _) in enumerate(directos):
            sale[i].append(x[a])
            entra[j].append(x[a])
        for a, (i, j, _) in enumerate(recargas):
            sale[i].append(y[a])
            entra[j].append(y[a])
        llegadas = defaultdict(list)
        for j, t in enumerate(trips):
            (km_ini, _), finales = ext[j]
            model.addConstr(u[j] + gp.quicksum(entra[j]) == 1)
            model.addConstr(gp.quicksum(v[j, f] for _, f in finales) + gp.quicksum(sale[j]) == 1)
            model.addGenConstrIndicator(u[j], True, e[j] <= BATERIA - CONSUMO * (km_ini + t['distancia_servicio_km']))
            for km_fin, f in finales:
                model.addGenConstrIndicator(v[j, f], True, e[j] - CONSUMO * km_fin >= RESERVA)
                if f in physical:
                    llegadas[f].append((t['fin_s'] + d['S:' + t['fin_stop_id'], f][1], v[j, f]))
        for a, (i, j, km) in enumerate(directos):
            model.addGenConstrIndicator(x[a], True, e[j] <= e[i] - CONSUMO * (km + trips[j]['distancia_servicio_km']))
        for a, (i, j, c) in enumerate(recargas):
            model.addConstr(q[a] <= c['maxq'] * y[a])
            model.addGenConstrIndicator(y[a], True, e[i] - CONSUMO * c['km1'] >= RESERVA)
            model.addGenConstrIndicator(y[a], True, e[i] - CONSUMO * c['km1'] + q[a] <= BATERIA)
            model.addGenConstrIndicator(y[a], True, e[j] <= e[i] + q[a]
                                        - CONSUMO * (c['km1'] + c['km2'] + trips[j]['distancia_servicio_km']))
        capacidades = 0 if podar else _capacidades(model, recargas, y, llegadas, physical, plugs)
        km = (gp.quicksum(ext[j][0][0] * u[j] for j in range(n))
              + gp.quicksum(km_fin * v[j, f] for j in range(n) for km_fin, f in ext[j][1])
              + gp.quicksum(km_ * x[a] for a, (_, _, km_) in enumerate(directos))
              + gp.quicksum((c['km1'] + c['km2']) * y[a] for a, (_, _, c) in enumerate(recargas))
              + sum(t['distancia_servicio_km'] for t in trips))
        model.setObjective(COSTO_BUS * u.sum() + COSTO_KM * km
                           + gp.quicksum(COSTO_SESION * y[a] + c['price'] * q[a] for a, (_, _, c) in enumerate(recargas)))
        model.optimize()
        info = dict(estado=int(model.Status), optimo=model.Status == gp.GRB.OPTIMAL and model.MIPGap <= gap + 1e-9,
                    variables=model.NumVars, restricciones=model.NumConstrs + model.NumGenConstrs,
                    restricciones_capacidad=capacidades, enlaces_directos=len(directos), enlaces_recarga=len(recargas),
                    tiempo_solver_s=model.Runtime)
        if model.SolCount == 0:
            try:  # sin plan, la cota existe solo si Gurobi alcanzó a resolver la relajación inicial
                info['cota_usd'] = model.ObjBound
            except gp.GurobiError:
                pass
            return None, info
        info.update(objetivo_usd=model.ObjVal, cota_usd=model.ObjBound, brecha=model.MIPGap)
        return _jornadas(trips, ext, directos, recargas, u, v, x, y, q, calendar, d), info
    finally:
        model.dispose()
