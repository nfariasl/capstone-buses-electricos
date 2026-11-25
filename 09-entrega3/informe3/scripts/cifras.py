"""Genera cifras.tex (una macro por cifra) y las tablas de tablas/ desde los resultados de la Entrega 3.

Ninguna cifra del informe se escribe a mano: el texto usa estas macros y las tablas se incluyen con
\\input. Cada bloque dice de qué archivo sale.
"""
import json
import statistics
import sys
from collections import defaultdict

import fuentes
from formato import con_signo, macro, numero

AQUI = fuentes.INFORME
DIAS = {'L': 'Laboral', 'S': 'Sabado', 'D': 'Domingo'}
ELECTROTERMINALES = {'E1': 'Uno', 'E2': 'Dos', 'E3': 'Tres', 'E4': 'Cuatro', 'E5': 'Cinco'}
NOMBRES_E = {'E1': 'Vespucio Norte', 'E2': 'El Conquistador', 'E3': 'Los Espinos', 'E4': 'La Reina',
             'E5': 'Santa Rosa'}
PRESUPUESTO_FINAL = 2400.0
PRESUPUESTO_CHICOS = 120.0
METODOS = [('pares', '', 'Pares'), ('pares_trios', '', 'Pares + tríos'),
           ('trios', 'parecidos', 'Tríos parecidos'), ('trios', 'azar', 'Tríos al azar'),
           ('cuartetos', 'parecidos', 'Cuartetos parecidos'), ('cuartetos', 'azar', 'Cuartetos al azar'),
           ('quintetos', 'parecidos', 'Quintetos parecidos'), ('quintetos', 'azar', 'Quintetos al azar'),
           ('octetos', 'parecidos', 'Octetos parecidos'), ('octetos', 'azar', 'Octetos al azar'),
           ('mezcla', 'parecidos', 'Mezcla creciente parecida'), ('mezcla', 'azar', 'Mezcla creciente al azar')]
CLAVE_METODO = {('pares', ''): 'Pares', ('pares_trios', ''): 'ParesTrios', ('trios', 'azar'): 'TriosAzar',
                ('cuartetos', 'azar'): 'Cuartetos', ('quintetos', 'azar'): 'QuintetosAzar',
                ('octetos', 'azar'): 'OctetosAzar', ('mezcla', 'azar'): 'MezclaAzar',
                ('cuartetos', 'parecidos'): 'CuartetosParecidos'}


def f(x):
    return float(x)


def pct(nuevo, base):
    return 100 * (nuevo / base - 1)


# ---------------------------------------------------------------- datos (instancias de la red completa)
def bloque_datos(m):
    for dia, nombre in DIAS.items():
        carpeta = fuentes.INSTANCIAS[dia]
        corridas = fuentes.leer_csv(carpeta / 'corridas.csv')
        eventos = []
        for c in corridas:
            eventos += [(int(c['inicio_s']), 1), (int(c['fin_s']), -1)]
        eventos.sort(key=lambda e: (e[0], e[1]))
        activos, pico, hora = 0, 0, 0
        for t, d in eventos:
            activos += d
            if activos > pico:
                pico, hora = activos, t
        km = sum(f(c['distancia_servicio_km']) for c in corridas)
        m['Corridas' + nombre] = numero(len(corridas))
        m['Rutas' + nombre] = numero(len({c['route_id'] for c in corridas}))
        m['Patrones' + nombre] = numero(len({c['trip_id'] for c in corridas}))
        m['KmServicio' + nombre] = numero(km)
        m['EnergiaServicioMwh' + nombre] = numero(km * 1.4 / 1000)
        m['KmMedio' + nombre] = numero(km / len(corridas), 1)
        m['DuracionMedia' + nombre] = numero(statistics.mean(int(c['fin_s']) - int(c['inicio_s'])
                                                             for c in corridas) / 60, 1)
        m['Simultaneidad' + nombre] = numero(pico)
        m['HoraSimultaneidad' + nombre] = f'{(hora // 3600) % 24:02d}:{(hora % 3600) // 60:02d}'
        if dia == 'L':
            m['_pico_L'] = pico
            m['_km_L'] = km
            por_sector = defaultdict(set)
            for c in corridas:
                por_sector[c['sector_id']].add(c['route_id'])
            for s, rutas in por_sector.items():
                m['RutasSector' + ELECTROTERMINALES['E' + s]] = numero(len(rutas))
            esc = json.loads(fuentes.leer_texto(carpeta / 'escenario.json'))
            p = esc['parametros']
            m['Bateria'], m['Reserva'] = numero(p['bateria_kwh']), numero(p['reserva_kwh'])
            m['PctReserva'] = numero(100 * p['reserva_kwh'] / p['bateria_kwh'])
            m['Consumo'], m['Potencia'] = numero(p['consumo_kwh_km'], 1), numero(p['potencia_kw'])
            m['EnergiaBloque'] = numero(p['potencia_kw'] * p['bloque_s'] / 3600)
            m['MinutosBloque'] = numero(p['bloque_s'] / 60)
            m['Autonomia'] = numero((p['bateria_kwh'] - p['reserva_kwh']) / p['consumo_kwh_km'])
            m['AutonomiaNominal'] = numero(p['bateria_kwh'] / p['consumo_kwh_km'])
            m['CostoBus'], m['CostoKmUnit'] = numero(p['costo_bus']), numero(p['costo_km'], 1)
            m['CostoSesion'], m['VelocidadVacio'] = numero(p['costo_sesion']), numero(p['velocidad_vacio_kmh'])
            precios = [t[2] for t in esc['tarifas']]
            m['TarifaMin'], m['TarifaMax'] = numero(min(precios), 2), numero(max(precios), 2)
            m['PlazasTotales'] = numero(sum(esc['capacidad_fisica'].values()))
            m['ConexionesTotales'] = numero(sum(esc['conexiones'].values()))
            m['MwInstalados'] = numero(sum(esc['conexiones'].values()) * p['potencia_kw'] / 1000)
            for e, n in esc['capacidad_fisica'].items():
                m['Plazas' + ELECTROTERMINALES[e]] = numero(n)
            m['_params'] = p
            m['_params_tarifas'] = esc['tarifas']


# ---------------------------------------------------------------- red completa, todos los métodos
def promedios(filas, presupuesto):
    grupos = defaultdict(list)
    for r in filas:
        if f(r['presupuesto_s']) == presupuesto:
            grupos[(r['metodo'], r['seleccion'])].append(r)
    return {k: dict(buses=statistics.mean(f(x['buses']) for x in v),
                    costo=statistics.mean(f(x['costo_total_usd']) for x in v),
                    n=len(v), filas=v) for k, v in grupos.items()}


def bloque_red_completa(m, tablas):
    costos_semana = {'base': 0.0, 'plan': 0.0}
    resultados = {}
    for dia, nombre in DIAS.items():
        filas = fuentes.leer_csv(fuentes.OCTETOS / f'red_completa_417_{dia}.csv')
        inicial = promedios(filas, 0.0)[('solo_base', '')]
        final = promedios(filas, PRESUPUESTO_FINAL)
        cuartetos = final[('cuartetos', 'azar')]
        resultados[dia] = (filas, final)
        m['BusesPlan' + nombre] = numero(cuartetos['buses'])
        m['CostoPlan' + nombre] = numero(cuartetos['costo'])
        m['BusesInicial' + nombre] = numero(inicial['buses'])
        m['CostoInicial' + nombre] = numero(inicial['costo'])
        m['MejoraInicial' + nombre] = con_signo(pct(cuartetos['costo'], inicial['costo']), 2)
        m['SemillasPlan' + nombre] = numero(cuartetos['n'])
        buses_semillas = sorted(f(x['buses']) for x in cuartetos['filas'])
        m['BusesSemillaMin' + nombre] = numero(buses_semillas[0])
        m['BusesSemillaMax' + nombre] = numero(buses_semillas[-1])
        m['_plan_' + dia] = cuartetos
        if dia == 'L':
            m['IntentosCuartetos'] = numero(statistics.mean(f(x['intentos']) for x in cuartetos['filas']))
            m['MejorasCuartetos'] = numero(statistics.mean(f(x['mejoras']) for x in cuartetos['filas']))
            m['SegundosInicial'] = numero(f(inicial['filas'][0]['tiempo_s']), 1)
        m['_inicial_' + dia] = inicial
    kpi = {r['kpi']: r for r in fuentes.leer_csv(fuentes.KPI / 'kpi_planes.csv')}
    for dia, nombre in DIAS.items():
        base_buses = f(kpi['buses'][f'caso_base_{dia}'])
        base_costo = f(kpi['costo_total_usd'][f'caso_base_{dia}'])
        plan = m['_plan_' + dia]
        m['BusesBase' + nombre], m['CostoBase' + nombre] = numero(base_buses), numero(base_costo)
        m['DeltaBuses' + nombre] = con_signo(plan['buses'] - base_buses)
        m['DeltaPctBuses' + nombre] = con_signo(pct(plan['buses'], base_buses), 1)
        m['DeltaCosto' + nombre] = con_signo(plan['costo'] - base_costo)
        m['DeltaPctCosto' + nombre] = con_signo(pct(plan['costo'], base_costo), 1)
        m['AhorroBuses' + nombre] = numero(base_buses - plan['buses'])
        m['AhorroCosto' + nombre] = numero(base_costo - plan['costo'])
        veces = 5 if dia == 'L' else 1
        costos_semana['base'] += veces * base_costo
        costos_semana['plan'] += veces * plan['costo']
        inicial = m['_inicial_' + dia]
        m['DeltaPctBusesInicial' + nombre] = con_signo(pct(inicial['buses'], base_buses), 1)
        m['DeltaPctCostoInicial' + nombre] = con_signo(pct(inicial['costo'], base_costo), 1)
        if dia == 'L':
            m['PctAhorroInicial'] = numero(100 * (base_buses - inicial['buses']) / (base_buses - plan['buses']))
    m['CostoSemanaBase'], m['CostoSemanaPlan'] = numero(costos_semana['base']), numero(costos_semana['plan'])
    m['CostoSemanaBaseMillones'] = numero(costos_semana['base'] / 1e6, 2)
    m['CostoSemanaPlanMillones'] = numero(costos_semana['plan'] / 1e6, 2)
    m['AhorroSemana'] = numero(costos_semana['base'] - costos_semana['plan'])
    m['AhorroSemanaMillones'] = numero((costos_semana['base'] - costos_semana['plan']) / 1e6, 2)
    m['DeltaPctSemana'] = con_signo(pct(costos_semana['plan'], costos_semana['base']), 1)

    filas_l, final_l = resultados['L']
    for clave, nombre in CLAVE_METODO.items():
        r = final_l[clave]
        m['BusesMetodo' + nombre], m['CostoMetodo' + nombre] = numero(r['buses']), numero(r['costo'])
    lineas = []
    por_presupuesto = {p: promedios(filas_l, p) for p in (600.0, 1200.0, 2400.0)}
    for metodo, seleccion, etiqueta in METODOS:
        celdas = []
        for p in (600.0, 1200.0, 2400.0):
            r = por_presupuesto[p].get((metodo, seleccion))
            celdas.append(numero(r['buses']) if r else '---')
        r = por_presupuesto[2400.0][(metodo, seleccion)]
        fila = [etiqueta, *celdas, numero(r['costo']), str(r['n'])]
        lineas.append(' & '.join(fila) + r' \\')
    tablas['metodos_red'] = '\n'.join(lineas)
    m['_metodos_presupuesto'] = {f'{k[0]}|{k[1]}': {str(p): por_presupuesto[p][k]['buses']
                                                     for p in por_presupuesto if k in por_presupuesto[p]}
                                 for k in por_presupuesto[2400.0]}
    semillas_1200 = [f(x['costo_total_usd']) for x in por_presupuesto[1200.0][('cuartetos', 'azar')]['filas']]
    m['RuidoSemillas'] = numero(100 * (max(semillas_1200) / min(semillas_1200) - 1), 2)
    m['MinutosFinal'] = numero(PRESUPUESTO_FINAL / 60)
    m['_kpi'] = kpi


# ---------------------------------------------------------------- KPI, composición y energía
def bloque_kpi(m, tablas):
    kpi = m['_kpi']
    for dia, nombre in DIAS.items():
        for plan, sufijo in (('caso_base', 'Base'), ('metodo', 'Plan')):
            col = f'{plan}_{dia}'

            def g(k):
                return f(kpi[k][col])
            s = sufijo + nombre
            m['BusesKpi' + s] = numero(g('buses'))
            m['CostoKpi' + s] = numero(g('costo_total_usd'))
            m['PctVacio' + s] = numero(g('pct_km_vacio'), 1)
            m['KmVacio' + s] = numero(g('km_vacio'))
            m['CorridasPorBus' + s] = numero(g('corridas_por_bus'), 1)
            for comp, k in (('Flota', 'buses'), ('Km', 'km'), ('Energia', 'energia'), ('Sesiones', 'sesiones')):
                m[f'Costo{comp}{s}'] = numero(g(f'costo_{k}_usd'))
                m[f'Pct{comp}{s}'] = numero(g(f'pct_costo_{k}'), 1)
            m['EnergiaCargada' + s] = numero(g('energia_cargada_kwh'))
            m['PctEnergiaCargada' + s] = numero(g('pct_energia_cargada'), 1)
            m['Sesiones' + s] = numero(g('sesiones'))
            m['EnergiaFinal' + s] = numero(g('energia_final_media_kwh'))
            m['EnergiaReponerMwh' + s] = numero(g('energia_a_reponer_kwh') / 1000)
            m['CargasSimultaneas' + s] = numero(g('cargas_simultaneas_max'))
            m['BusesTerminanE' + s] = numero(g('buses_terminan_en_E'))
            m['CostoPorCorrida' + s] = numero(g('costo_por_corrida_usd'), 1)
            m['PrecioMedioKwh' + s] = numero(g('costo_energia_usd') / g('energia_cargada_kwh'), 3)
            m['KwhPorSesion' + s] = numero(g('kwh_por_sesion'))
    ahorro = {(r['dia'], r['kpi']): r for r in fuentes.leer_csv(fuentes.KPI / 'kpi_ahorro.csv')}
    total = -f(ahorro['L', 'costo_total_usd']['diferencia'])
    m['_componentes'] = {}
    for comp, k in (('Flota', 'costo_buses_usd'), ('Km', 'costo_km_usd'), ('Energia', 'costo_energia_usd'),
                    ('Sesiones', 'costo_sesiones_usd')):
        dif = -f(ahorro['L', k]['diferencia'])
        m['_componentes'][comp] = dif
        m['AhorroComp' + comp] = numero(dif)
        m['PctAhorroComp' + comp] = numero(100 * dif / total, 1)
        m['DeltaPctComp' + comp] = con_signo(f(ahorro['L', k]['pct']), 1)
    for dia, nombre in DIAS.items():
        m['DeltaPctVacio' + nombre] = con_signo(f(ahorro[dia, 'km_vacio']['pct']), 1)
        m['DeltaPctEnergiaCargada' + nombre] = con_signo(f(ahorro[dia, 'energia_cargada_kwh']['pct']), 1)
    uso = fuentes.leer_csv(fuentes.KPI / 'uso_e_resumen.csv')
    for plan, sufijo in (('caso_base_L', 'Base'), ('metodo_L', 'Plan'), ('metodo_S', 'PlanSabado')):
        filas = [r for r in uso if r['plan'] == plan]
        maximo = max(filas, key=lambda r: f(r['buses_cargando_max']))
        m['PicoCargando' + sufijo] = numero(f(maximo['buses_cargando_max']))
        m['HoraPicoCargando' + sufijo] = maximo['hora_pico']
        m['PicoCargandoE' + sufijo] = NOMBRES_E[maximo['electroterminal']]
        pcts = [f(r['pct_conexiones_max']) for r in filas]
        m['PctConexionesMin' + sufijo], m['PctConexionesMax' + sufijo] = numero(min(pcts)), numero(max(pcts))
        m['PctConexionesMaxE' + sufijo] = NOMBRES_E[max(filas, key=lambda r: f(r['pct_conexiones_max']))['electroterminal']]
        m['CargandoMin' + sufijo] = numero(min(f(r['buses_cargando_max']) for r in filas))
        horas = sorted(r['hora_pico'] for r in filas)
        m['HoraPicoMin' + sufijo], m['HoraPicoMax' + sufijo] = horas[0], horas[-1]
        m['ElectroterminalesLlenos' + sufijo] = numero(sum(f(r['pct_conexiones_max']) >= 100 for r in filas))
    plazas = fuentes.leer_csv(fuentes.KPI / 'plazas_metodo_L_resumen.csv')
    sin_cierre = [f(r['pct_plazas_max_sin_cierre']) for r in plazas]
    m['PctPlazasOperacionMin'], m['PctPlazasOperacionMax'] = numero(min(sin_cierre)), numero(max(sin_cierre))
    minutos = [f(r['minutos_al_100']) for r in plazas]
    m['MinutosPlazasLlenasMin'], m['MinutosPlazasLlenasMax'] = numero(min(minutos)), numero(max(minutos))
    plazas_s = fuentes.leer_csv(fuentes.KPI / 'plazas_metodo_S_resumen.csv')
    m['PctPlazasOperacionMaxSabado'] = numero(max(f(r['pct_plazas_max_sin_cierre']) for r in plazas_s))
    perfil = fuentes.leer_csv(fuentes.KPI / 'uso_e_perfil.csv')
    tarifas = m['_params_tarifas']
    punta = max(t[2] for t in tarifas)
    m['_energia_hora'] = {}
    for plan, sufijo in (('caso_base_L', 'Base'), ('metodo_L', 'Plan')):
        por_hora = defaultdict(float)
        for r in perfil:
            if r['plan'] == plan:
                por_hora[int(r['hora']) % 24] += f(r['carga_kwh'])
        total_kwh = sum(por_hora.values())
        en_punta = sum(e for h, e in por_hora.items() if any(a <= h < b and p == punta for a, b, p in tarifas))
        m['PctEnergiaPunta' + sufijo] = numero(100 * en_punta / total_kwh)
        hora = max(por_hora, key=por_hora.get)
        m['HoraMasCarga' + sufijo] = f'{hora}'
        m['HoraMasCargaFin' + sufijo] = f'{hora + 1}'
        m['_energia_hora'][sufijo] = [100 * por_hora[h] / total_kwh for h in range(24)]
    sectores = fuentes.leer_csv(fuentes.KPI / 'kpi_por_sector.csv')
    base = {r['sector']: r for r in sectores if r['plan'] == 'caso_base_L'}
    lineas, propias = [], []
    for r in sorted((r for r in sectores if r['plan'] == 'metodo_L'), key=lambda r: r['sector']):
        b = base[r['sector']]
        e = 'E' + r['sector']
        propias.append((f(r['pct_carga_en_su_electroterminal']), r['electroterminal']))
        lineas.append(' & '.join([f"{e} {r['electroterminal']}", m['RutasSector' + ELECTROTERMINALES[e]],
                                  numero(f(r['corridas'])), numero(f(b['buses'])), numero(f(r['buses'])),
                                  con_signo(pct(f(r['buses']), f(b['buses'])), 1),
                                  numero(f(r['pct_carga_en_su_electroterminal']), 1)]) + r' \\')
        m['PctCargaPropia' + ELECTROTERMINALES[e]] = numero(f(r['pct_carga_en_su_electroterminal']), 1)
        m['BusesPlanSector' + ELECTROTERMINALES[e]] = numero(f(r['buses']))
    tablas['sectores'] = '\n'.join(lineas)
    tamanos = [int(f(r['corridas'])) for r in sectores if r['plan'] == 'metodo_L']
    m['ParesSectorMillones'] = numero(sum(n * (n - 1) / 2 for n in tamanos) / 1e6)
    otros = sorted(p for p, n in propias if n != 'Los Espinos')
    m['PctCargaPropiaOtrosMin'], m['PctCargaPropiaOtrosMax'] = numero(otros[0], 1), numero(otros[-1], 1)
    cruce = {r['sector']: r for r in fuentes.leer_csv(fuentes.KPI / 'uso_e_sector_x_electroterminal.csv')
             if r['plan'] == 'metodo_L'}
    m['PctEspinosEnDos'] = numero(f(cruce['3']['pct_en_E2']), 1)
    m['PctEspinosEnCinco'] = numero(f(cruce['3']['pct_en_E5']), 1)
    m['PctEspinosEnUno'] = numero(f(cruce['3']['pct_en_E1']), 1)
    m['PctVespucioEnTres'] = numero(f(cruce['1']['pct_en_E3']), 1)
    m['PctReinaEnUno'] = numero(f(cruce['4']['pct_en_E1']), 1)


# ---------------------------------------------------------------- calidad: brechas al óptimo
SUFIJO_CASO = {'rutas_06': ('6 rutas', 'Seis'), 'rutas_08': ('8 rutas', 'Ocho'), 'mediano_200': ('Mediano', 'Mediano'),
               'rutas_10': ('10 rutas', 'Diez'), 'rutas_12': ('12 rutas', 'Doce')}


def bloque_calidad(m, tablas):
    exacta = {r['instancia']: r for r in fuentes.leer_csv(fuentes.OCTETOS / 'casos_chicos_exacta.csv')}
    if not all(r['optimo'] == 'True' for r in exacta.values()):
        raise ValueError('Algún caso chico no tiene óptimo demostrado')
    filas = fuentes.leer_csv(fuentes.OCTETOS / 'casos_chicos.csv')
    corridas = sorted(int(r['corridas']) for r in exacta.values())
    minutos = sorted(f(r['tiempo_s']) / 60 for r in exacta.values())
    m['CasosChicos'] = numero(len(exacta))
    m['CorridasChicosMin'], m['CorridasChicosMax'] = numero(corridas[0]), numero(corridas[-1])
    m['MinutosExactaMin'], m['MinutosExactaMax'] = numero(minutos[0]), numero(minutos[-1])
    m['SegundosChicos'] = numero(PRESUPUESTO_CHICOS)
    brechas = defaultdict(lambda: defaultdict(list))
    for r in filas:
        if f(r['presupuesto_s']) in (PRESUPUESTO_CHICOS, 0.0):
            opt = f(exacta[r['instancia']]['costo_total_usd'])
            brechas[(r['metodo'], r['seleccion'])][r['instancia']].append(pct(f(r['costo_total_usd']), opt))
    lineas = []
    m['_brechas'] = {}
    for metodo, seleccion, etiqueta in [('solo_base', '', 'Plan inicial (sin mejora)')] + METODOS:
        por_caso = brechas[(metodo, seleccion)]
        media = statistics.mean(statistics.mean(v) for v in por_caso.values())
        peor = max(x for v in por_caso.values() for x in v)
        m['_brechas'][etiqueta] = media
        fila = [etiqueta, numero(media, 2), numero(peor, 2)]
        if (metodo, seleccion) == ('cuartetos', 'azar'):
            m['BrechaCuartetos'], m['BrechaPeorCuartetos'] = numero(media, 2), numero(peor, 2)
        if (metodo, seleccion) == ('solo_base', ''):
            m['BrechaInicial'], m['BrechaPeorInicial'] = numero(media, 2), numero(peor, 2)
        if (metodo, seleccion) == ('pares_trios', ''):
            m['BrechaParesTrios'], m['BrechaPeorParesTrios'] = numero(media, 2), numero(peor, 2)
        if (metodo, seleccion) == ('pares', ''):
            m['BrechaPares'] = numero(media, 2)
        lineas.append(' & '.join(fila) + r' \\')
    tablas['brecha_chicos'] = '\n'.join(lineas)

    exacta_r = {r['instancia']: r for r in fuentes.leer_csv(fuentes.OCTETOS / 'casos_rutas_exacta.csv')
                + fuentes.leer_csv(fuentes.OCTETOS / 'casos_medianos_exacta_podada.csv')}
    heur = (fuentes.leer_csv(fuentes.OCTETOS / 'casos_rutas.csv')
            + fuentes.leer_csv(fuentes.OCTETOS / 'casos_medianos.csv'))
    por_caso = defaultdict(dict)
    for r in heur:
        por_caso[r['instancia']][r['metodo']] = r
    lineas = []
    for inst in sorted(por_caso, key=lambda k: (int(next(iter(por_caso[k].values()))['corridas']), k)):
        h = por_caso[inst]
        etiqueta, sufijo = next(v for k, v in SUFIJO_CASO.items() if inst.startswith(k))
        n_corr = int(next(iter(h.values()))['corridas'])
        m['CorridasRutas' + sufijo] = numero(n_corr)
        con_optimo = inst in exacta_r and exacta_r[inst]['optimo'] == 'True'
        if con_optimo:
            opt = exacta_r[inst]
            ref = f(opt['costo_total_usd'])
            celdas = [f"{numero(f(opt['buses']))} · {numero(ref)}"]
            m['BusesOptRutas' + sufijo] = numero(f(opt['buses']))
        else:
            ref = f(h['solo_base']['costo_total_usd'])
            celdas = ['sin óptimo']
            m['BusesInicialRutas' + sufijo] = numero(f(h['solo_base']['buses']))
        for met, nm in (('solo_base', 'Inicial'), ('pares_trios', 'ParesTrios'), ('cuartetos', 'Cuartetos')):
            r = h.get(met)
            if r is None:
                celdas.append('---')
                continue
            if met == 'solo_base' and not con_optimo:
                celdas.append(f"({numero(f(r['buses']))})")
                continue
            dif = pct(f(r['costo_total_usd']), ref)
            celdas.append(f"{con_signo(dif, 2)} ({numero(f(r['buses']))})")
            m[f'Brecha{nm}Rutas{sufijo}'] = con_signo(dif, 2)
            m[f'Buses{nm}Rutas{sufijo}'] = numero(f(r['buses']))
        lineas.append(' & '.join([etiqueta, numero(n_corr), *celdas]) + r' \\')
    tablas['casos_rutas'] = '\n'.join(lineas)

    lineas = []
    for bat in (150, 120):
        exa = {r['instancia']: r for r in fuentes.leer_csv(fuentes.OCTETOS / f'recarga_bat{bat}_exacta.csv')}
        heu = fuentes.leer_csv(fuentes.OCTETOS / f'recarga_bat{bat}.csv')
        difs, mejoras, brechas_cota = [], [], []
        for inst in sorted(exa, key=lambda k: int(exa[k]['corridas'])):
            candidatos = [r for r in heu if r['instancia'] == inst and r['metodo'] != 'solo_base']
            if not candidatos:
                continue
            mejor = min(candidatos, key=lambda r: f(r['costo_total_usd']))
            inicial = next(r for r in heu if r['instancia'] == inst and r['metodo'] == 'solo_base')
            e = exa[inst]
            dif = pct(f(mejor['costo_total_usd']), f(e['costo_total_usd']))
            grande = 'rutas_10' in inst
            if not grande:
                difs.append(dif)
                mejoras.append(pct(f(mejor['costo_total_usd']), f(inicial['costo_total_usd'])))
                brechas_cota.append(pct(f(e['costo_total_usd']), f(e['cota_usd'])))
            caso = '10 rutas' if grande else f"Chico {int(inst.split('_')[2])}"
            lineas.append(' & '.join([f'{bat}', caso, numero(int(e['corridas'])), numero(f(inicial['buses'])),
                                      f"{numero(f(e['buses']))} · {numero(f(e['costo_total_usd']))}",
                                      numero(pct(f(e['costo_total_usd']), f(e['cota_usd'])), 1),
                                      f"{numero(f(mejor['buses']))} · {numero(f(mejor['costo_total_usd']))}",
                                      con_signo(dif, 1)]) + r' \\')
            if grande:
                m['BusesExactaGrande'] = numero(f(e['buses']))
                m['CostoExactaGrande'] = numero(f(e['costo_total_usd']))
                m['BusesHeurGrande'] = numero(f(mejor['buses']))
                m['CostoHeurGrande'] = numero(f(mejor['costo_total_usd']))
                m['BusesInicialGrande'] = numero(f(inicial['buses']))
                m['CostoInicialGrande'] = numero(f(inicial['costo_total_usd']))
                m['DifGrande'] = con_signo(dif, 1)
                m['CorridasGrande'] = numero(int(e['corridas']))
        nom = {150: 'CientoCincuenta', 120: 'CientoVeinte'}[bat]
        m['DifMediaRecarga' + nom] = con_signo(statistics.mean(difs), 1)
        m['DifMaxRecarga' + nom] = con_signo(max(difs), 1)
        m['DifMinRecarga' + nom] = numero(min(difs), 1)
        m['MejoraRecargaMin' + nom] = numero(-max(mejoras))
        m['MejoraRecargaMax' + nom] = numero(-min(mejoras))
        m['BrechaCotaRecargaMin' + nom] = numero(min(brechas_cota), 1)
        m['BrechaCotaRecargaMax' + nom] = numero(max(brechas_cota), 1)
        if bat == 150:
            lineas.append(r'\midrule')
    tablas['recarga_forzada'] = '\n'.join(lineas)

    p = m['_params']
    cota = m['_pico_L'] * p['costo_bus'] + p['costo_km'] * m['_km_L']
    plan = m['_plan_L']
    m['CotaCosto'] = numero(cota)
    m['BrechaCotaCosto'] = numero(pct(plan['costo'], cota), 1)
    m['BrechaCotaBuses'] = numero(pct(plan['buses'], m['_pico_L']), 1)


# ---------------------------------------------------------------- sensibilidad
ETIQUETAS_SENS = {'cierre_E1': 'Cierre de E1 Vespucio Norte', 'cierre_E2': 'Cierre de E2 El Conquistador',
                  'cierre_E3': 'Cierre de E3 Los Espinos', 'cierre_E4': 'Cierre de E4 La Reina',
                  'cierre_E5': 'Cierre de E5 Santa Rosa', 'plazas_-20': 'Plazas y conexiones $-$20\\,\\%',
                  'plazas_+20': 'Plazas y conexiones +20\\,\\%', 'plazas_+50': 'Plazas y conexiones +50\\,\\%',
                  'conexiones_-50': 'Mitad de las conexiones', 'plazas_por_demanda': 'Plazas según demanda',
                  'tarifa_punta_+50': 'Tarifa de punta +50\\,\\%'}
CLAVES_SENS = {'cierre_E1': 'CierreUno', 'cierre_E2': 'CierreDos', 'cierre_E3': 'CierreTres',
               'cierre_E4': 'CierreCuatro', 'cierre_E5': 'CierreCinco', 'plazas_-20': 'PlazasMenosVeinte',
               'plazas_+20': 'PlazasMasVeinte', 'plazas_+50': 'PlazasMasCincuenta',
               'conexiones_-50': 'MitadConexiones', 'plazas_por_demanda': 'PlazasDemanda',
               'tarifa_punta_+50': 'TarifaPunta'}


def bloque_sensibilidad(m, tablas):
    filas = fuentes.leer_csv(fuentes.SENSIBILIDAD / 'tabla_sensibilidad.csv')
    cuart = {r['escenario']: r for r in filas if r['metodo'] == 'cuartetos'}
    ini = {r['escenario']: r for r in filas if r['metodo'] == 'solo_base'}
    m['BusesSensBase'] = numero(f(cuart['base']['buses']))
    m['CostoSensBase'] = numero(f(cuart['base']['costo_total_usd']))
    lineas = []
    orden = sorted((e for e in cuart if e != 'base'), key=lambda e: -f(cuart[e]['delta_costo_pct']))
    for e in orden:
        c, i = cuart[e], ini[e]
        lineas.append(' & '.join([ETIQUETAS_SENS[e], numero(f(c['buses'])), con_signo(f(c['delta_buses'])),
                                  con_signo(f(c['delta_costo_pct']), 2), con_signo(f(i['delta_buses'])),
                                  con_signo(f(i['delta_costo_pct']), 2)]) + r' \\')
        clave = CLAVES_SENS[e]
        m['SensBuses' + clave] = con_signo(f(c['delta_buses']))
        m['SensCosto' + clave] = con_signo(f(c['delta_costo_pct']), 2)
        m['SensCostoInicial' + clave] = con_signo(f(i['delta_costo_pct']), 2)
        m['SensUsdInicial' + clave] = numero(abs(f(i['delta_costo_usd'])))
        m['SensBusesInicial' + clave] = con_signo(f(i['delta_buses']))
    tablas['sensibilidad'] = '\n'.join(lineas)
    m['_sens'] = [(ETIQUETAS_SENS[e], f(cuart[e]['delta_costo_pct']), f(ini[e]['delta_costo_pct'])) for e in orden]

    fis = {(r['instancia'], r['metodo']): r for r in fuentes.leer_csv(fuentes.SENSIBILIDAD / 'fisicos_417_L.csv')}
    ahorro = {r['escenario']: r for r in fuentes.leer_csv(fuentes.SENSIBILIDAD / 'ahorro_fisicos.csv')}
    base_c = fis['instancia_417', 'cuartetos']
    m['BusesFisBase'] = numero(f(base_c['buses']))
    etiquetas = {'instancia_417': 'Base de la tanda', 'bateria_300': 'Batería de 300 kWh',
                 'bateria_250': 'Batería de 250 kWh', 'consumo_+10': 'Consumo +10\\,\\%',
                 'consumo_+20': 'Consumo +20\\,\\%'}
    nombres = {'instancia_417': 'Base', 'bateria_300': 'BatTrescientos', 'bateria_250': 'BatDoscientosCincuenta',
               'consumo_+10': 'ConsumoDiez', 'consumo_+20': 'ConsumoVeinte'}
    lineas = []
    for esc in ('instancia_417', 'bateria_300', 'bateria_250', 'consumo_+10', 'consumo_+20'):
        c, a = fis[esc, 'cuartetos'], ahorro[esc]
        es_base = esc == 'instancia_417'
        db = '---' if es_base else con_signo(pct(f(c['buses']), f(base_c['buses'])), 1)
        dc = '---' if es_base else con_signo(pct(f(c['costo_total_usd']), f(base_c['costo_total_usd'])), 1)
        lineas.append(' & '.join([etiquetas[esc], numero(f(a['bateria_kwh'])), numero(f(a['consumo_kwh_km']), 2),
                                  numero(f(a['buses_caso_base'])), numero(f(c['buses'])), db, dc,
                                  con_signo(f(a['ahorro_costo_pct']), 1)]) + r' \\')
        n = nombres[esc]
        m['FisBuses' + n] = numero(f(c['buses']))
        m['FisBusesBase' + n] = numero(f(a['buses_caso_base']))
        m['FisDeltaBuses' + n], m['FisDeltaCosto' + n] = db, dc
        m['FisAhorroCosto' + n] = con_signo(f(a['ahorro_costo_pct']), 1)
    tablas['fisicos'] = '\n'.join(lineas)
    ahorros = [f(a['ahorro_costo_pct']) for a in ahorro.values()]
    m['FisAhorroMin'], m['FisAhorroMax'] = numero(-max(ahorros), 1), numero(-min(ahorros), 1)

    costos = fuentes.leer_csv(fuentes.SENSIBILIDAD / 'costos_evaluados.csv')
    lab = [f(r['ahorro_pct']) for r in costos if r['dia'] == 'L' and r['escenario'] != 'base']
    m['CostosAhorroMin'], m['CostosAhorroMax'] = numero(-max(lab), 2), numero(-min(lab), 2)
    nombres_c = {'base': 'Costos del enunciado', 'costo_bus_-20': 'Costo por bus $-$20\\,\\%',
                 'costo_bus_+20': 'Costo por bus +20\\,\\%', 'costo_km_-20': 'Costo por km $-$20\\,\\%',
                 'costo_km_+20': 'Costo por km +20\\,\\%'}
    por = defaultdict(dict)
    for r in costos:
        por[r['escenario']][r['dia']] = r
    lineas = [' & '.join([nombres_c[esc]] + [con_signo(f(por[esc][x]['ahorro_pct']), 2) for x in 'LSD']) + r' \\'
              for esc in nombres_c]
    espera = {(r['plan'], r['dia']): r for r in fuentes.leer_csv(fuentes.KPI / 'costo_espera.csv')}
    lineas.append(' & '.join(['Cobrando la espera']
                             + [con_signo(f(espera['metodo', x]['ahorro_con_espera_pct']), 2) for x in 'LSD']) + r' \\')
    tablas['costos'] = '\n'.join(lineas)
    m['AhorroConEspera'] = con_signo(f(espera['metodo', 'L']['ahorro_con_espera_pct']), 2)
    m['AhorroSinEspera'] = con_signo(f(espera['metodo', 'L']['ahorro_sin_espera_pct']), 2)
    m['PctEspera'] = numero(f(espera['metodo', 'L']['pct_espera']), 1)
    m['CostoEsperaPlan'] = numero(f(espera['metodo', 'L']['costo_espera_usd']))
    m['CostoEsperaBaseRed'] = numero(f(espera['caso_base', 'L']['costo_espera_usd']))
    params = {r['parameter']: r['value'] for r in fuentes.leer_csv(fuentes.RAIZ / '01-datos/parameters.csv')} \
        if (fuentes.RAIZ / '01-datos/parameters.csv').exists() else {}
    m['CostoEsperaMinuto'] = numero(float(params.get('waiting_cost_per_min', 0.03)), 2)
    m['FlotaDeclarada'] = numero(float(params.get('fleet_size', 1200)))
    m['PctFlotaDeclarada'] = numero(100 * float(params.get('fleet_size', 1200)) / m['_pico_L'])


# ---------------------------------------------------------------- incertidumbre y repetibilidad
def bloque_incertidumbre(m, tablas):
    filas = fuentes.leer_csv(fuentes.INCERTIDUMBRE / 'atrasos.csv')
    por = {(r['plan'], int(r['cv_pct'])): r for r in filas}
    m['ReplicasAtrasos'] = numero(int(filas[0]['replicas']))
    lineas = []
    m['_atrasos'] = {}
    for cv in sorted({k[1] for k in por}):
        b, p = por['caso_base', cv], por['metodo', cv]
        m['_atrasos'][cv] = (f(b['pct_atrasadas_5min']), f(p['pct_atrasadas_5min']))
        lineas.append(' & '.join([f'{cv}', numero(f(b['pct_atrasadas_5min']), 1), numero(f(p['pct_atrasadas_5min']), 1),
                                  numero(f(b['atraso_p95_min']), 1), numero(f(p['atraso_p95_min']), 1),
                                  numero(f(b['buses_bajo_reserva'])), numero(f(p['buses_bajo_reserva'])),
                                  numero(f(b['buses_sin_energia'])), numero(f(p['buses_sin_energia']))]) + r' \\')
        nombre = {10: 'Diez', 20: 'Veinte', 30: 'Treinta'}[cv]
        m['AtrasadasBase' + nombre] = numero(f(b['pct_atrasadas_5min']), 1)
        m['AtrasadasPlan' + nombre] = numero(f(p['pct_atrasadas_5min']), 1)
        m['BajoReservaBase' + nombre] = numero(f(b['buses_bajo_reserva']))
        m['BajoReservaPlan' + nombre] = numero(f(p['buses_bajo_reserva']))
        m['SinEnergiaPlan' + nombre] = numero(f(p['buses_sin_energia']))
        m['SinEnergiaBase' + nombre] = numero(f(b['buses_sin_energia']))
    tablas['atrasos'] = '\n'.join(lineas)

    rep = fuentes.leer_csv(fuentes.KPI / 'repetibilidad.csv')
    lineas = []
    for dia, nombre in DIAS.items():
        t = next(r for r in rep if r['plan'] == f'metodo_{dia}' and r['electroterminal'] == 'Total')
        b = next(r for r in rep if r['plan'] == f'caso_base_{dia}' and r['electroterminal'] == 'Total')
        etiqueta = {'L': 'Laboral', 'S': 'Sábado', 'D': 'Domingo'}[dia]
        lineas.append(' & '.join([etiqueta, numero(f(t['energia_a_reponer_mwh'])), numero(f(t['ventana_mediana_h']), 1),
                                  numero(f(t['pct_cubierto'])), numero(f(b['pct_cubierto'])),
                                  numero(f(t['mw_necesarios'])), numero(f(t['conexiones_necesarias'])),
                                  numero(f(t['conexiones_faltantes']))]) + r' \\')
        m['ReponerMwh' + nombre] = numero(f(t['energia_a_reponer_mwh']))
        m['ReponerGwh' + nombre] = numero(f(t['energia_a_reponer_mwh']) / 1000, 2)
        m['PctCubierto' + nombre] = numero(f(t['pct_cubierto']))
        m['PctCubiertoBase' + nombre] = numero(f(b['pct_cubierto']))
        m['VentanaMediana' + nombre] = numero(f(t['ventana_mediana_h']), 1)
        m['HorasTodasConexiones' + nombre] = numero(f(t['horas_con_todas_las_conexiones']), 1)
        m['MwNecesarios' + nombre] = numero(f(t['mw_necesarios']))
        m['ConexionesNecesarias' + nombre] = numero(f(t['conexiones_necesarias']))
        m['ConexionesFaltantes' + nombre] = numero(f(t['conexiones_faltantes']))
        m['ConexionesFaltantesBase' + nombre] = numero(f(b['conexiones_faltantes']))
        m['BusesTerminanFuera' + nombre] = numero(f(m['_kpi']['buses'][f'metodo_{dia}'])
                                                  - f(m['_kpi']['buses_terminan_en_E'][f'metodo_{dia}']))
    tablas['repetibilidad'] = '\n'.join(lineas)
    por_e = [r for r in rep if r['plan'] == 'metodo_L' and r['electroterminal'] != 'Total']
    peor = min(por_e, key=lambda r: f(r['pct_cubierto']))
    mejor = max(por_e, key=lambda r: f(r['pct_cubierto']))
    m['ReposPeorE'], m['ReposPeorPct'] = peor['nombre'], numero(f(peor['pct_cubierto']))
    m['ReposPeorFaltan'] = numero(f(peor['conexiones_faltantes']))
    m['ReposMejorE'], m['ReposMejorPct'] = mejor['nombre'], numero(f(mejor['pct_cubierto']))
    m['ReposMejorFaltan'] = numero(f(mejor['conexiones_faltantes']))
    mas = max(por_e, key=lambda r: f(r['conexiones_faltantes']))
    m['ReposMasFaltanE'], m['ReposMasFaltan'] = mas['nombre'], numero(f(mas['conexiones_faltantes']))
    m['ReposMasFaltanPct'] = numero(f(mas['pct_cubierto']))
    m['_repetibilidad'] = {r['electroterminal']: f(r['pct_cubierto']) for r in por_e}
    noche = {r['dia']: r for r in fuentes.leer_csv(fuentes.KPI / 'costo_recarga_nocturna.csv')}
    columnas = ('ahorro_noche_0.10_sin_sesion_pct', 'ahorro_noche_0.10_con_sesion_pct',
                'ahorro_noche_0.11_con_sesion_pct')
    for dia, nombre in list(DIAS.items()) + [('semana', 'Semana')]:
        valores = [f(noche[dia][c]) for c in columnas]
        m['AhorroNocheMin' + nombre] = numero(-max(valores), 1)
        m['AhorroNocheMax' + nombre] = numero(-min(valores), 1)
        m['ReponerBaseMwh' + nombre] = numero(f(noche[dia]['energia_base_mwh']))


# ---------------------------------------------------------------- informe 2 (evolución del método)
def bloque_informe2(m):
    dos = fuentes.macros_informe2()
    for clave in ('BusesBase', 'CostoBase', 'BusesModelo', 'CostoModelo', 'BusesConstruccion', 'BusesPrototipo',
                  'BusesPrototipoSinMejora', 'FlotaFaseUno', 'PisoFaseUno', 'BusesSinRecargas', 'CostoSinRecargas',
                  'BusesUmbralVeinte', 'BusesUmbralTreinta', 'BusesUmbralCincuenta', 'CostoUmbralVeinte',
                  'CostoUmbralTreinta', 'CostoUmbralCincuenta', 'RutasMuestra', 'CorridasMuestra',
                  'PctAhorroConstruccion', 'DeltaPctBuses', 'DeltaPctCosto', 'BusesExtraSinRecargas'):
        if clave not in dos:
            raise KeyError(f'Falta {clave} en el cifras.tex del informe 2')
        m['Edos' + clave] = dos[clave]
    entero = lambda s: int(s.replace('.', ''))  # noqa: E731
    fase1, sin, cons = entero(dos['FlotaFaseUno']), entero(dos['BusesPrototipoSinMejora']), entero(dos['BusesConstruccion'])
    m['EdosAumentoBateria'] = numero(sin - fase1)
    m['EdosPctAumentoBateria'] = numero(100 * (sin / fase1 - 1), 1)
    m['EdosEvitables'] = numero(sin - cons)


def bloque_terminales(m):
    """Ocupación máxima de los terminales comunes (09-entrega3/kpi/ocupacion_terminales.py)."""
    filas = fuentes.leer_csv(fuentes.KPI / 'ocupacion_terminales.csv')
    for plan, sufijo in (('metodo_L', 'Plan'), ('caso_base_L', 'Base')):
        valores = sorted(int(r['buses_max']) for r in filas if r['plan'] == plan)
        m['TerminalMin' + sufijo], m['TerminalMax' + sufijo] = numero(valores[0]), numero(valores[-1])
        m['TerminalSuma' + sufijo] = numero(sum(valores))


def bloque_entrega1(m):
    """Campos del diccionario de datos que no vienen en ningún archivo (análisis de datos de la Entrega 1)."""
    texto = fuentes.leer_texto(fuentes.RAIZ / '03-resultados/metricas.tex')
    valores = {}
    for linea in texto.splitlines():
        r = fuentes.MACRO.match(linea.strip())
        if r:
            valores[r.group(1)] = r.group(2)
    m['CamposDocumentados'] = valores['camposDocumentados']
    m['CamposAusentes'] = valores['camposAusentes']
    m['ListaCamposAusentes'] = valores['listaCamposAusentes']


def main():
    m, tablas = {}, {}
    bloque_entrega1(m)
    bloque_terminales(m)
    bloque_datos(m)
    bloque_red_completa(m, tablas)
    bloque_kpi(m, tablas)
    bloque_calidad(m, tablas)
    bloque_sensibilidad(m, tablas)
    bloque_incertidumbre(m, tablas)
    bloque_informe2(m)
    publicas = {k: v for k, v in m.items() if not k.startswith('_')}
    # Versión sin signo de cada variación porcentual, para frases como «baja un 15,4 %».
    for k, v in list(publicas.items()):
        if k.startswith('DeltaPct') and isinstance(v, str):
            publicas['Baja' + k[len('DeltaPct'):]] = v.replace('\\ensuremath{-}', '').lstrip('+')
    for k in ('DifMediaRecargaCientoCincuenta', 'DifMediaRecargaCientoVeinte', 'BrechaCuartetosRutasOcho'):
        publicas[k + 'Abs'] = publicas[k].lstrip('+')
    for k in ('RutasLaboral', 'CorridasLaboral', 'BusesPlanLaboral', 'BusesBaseLaboral', 'BajaBusesLaboral',
              'CostoPlanLaboral', 'BajaCostoLaboral', 'BajaSemana', 'BrechaCuartetos', 'BrechaCuartetosRutasOcho'):
        publicas[k + 'En'] = publicas[k].replace('.', '_').replace(',', '.').replace('_', ',').lstrip('+')
    texto = '% Generado por scripts/cifras.py. No editar a mano.\n' + '\n'.join(
        macro(n, v) for n, v in sorted(publicas.items())) + '\n'
    (AQUI / 'cifras.tex').write_text(texto, encoding='utf-8')
    (AQUI / 'tablas').mkdir(exist_ok=True)
    for nombre, cuerpo in tablas.items():
        (AQUI / 'tablas' / f'{nombre}.tex').write_text('% Generado por scripts/cifras.py.\n' + cuerpo + '\n',
                                                       encoding='utf-8')
    datos = {k.lstrip('_'): m[k] for k in ('_sens', '_repetibilidad', '_componentes', '_energia_hora',
                                            '_brechas', '_atrasos', '_metodos_presupuesto')}
    (AQUI / 'salidas').mkdir(exist_ok=True)
    (AQUI / 'salidas/para_figuras.json').write_text(json.dumps(datos, ensure_ascii=False, indent=1),
                                                    encoding='utf-8')
    print(f'{len(publicas)} macros en cifras.tex y {len(tablas)} tablas en tablas/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
