"""Un único MILP para recargas y terminales de hasta ocho secuencias fijas."""
import time
from collections import defaultdict
import numpy as np
import gurobipy as gp
from metodo_hibrido.recarga import opciones
from metodo_hibrido.calendario import actividad, esperar, agregar_viaje
from metodo_hibrido.energia import BATERIA, RESERVA

# Pares y tríos usan 2 y 3; el estudio de 09-entrega3/octetos llega a grupos de 8.
MAX_SECUENCIAS = 8

def acoplar(model, intervals, calendar, charging=False, max_buses=2):
    """Intervalos semiabiertos; restricciones exactas contra la ocupación ajena."""
    constraints=0
    for e, entries in intervals.items():
        events=defaultdict(list)
        for key,(s,f,var) in enumerate(entries):
            if f>s:
                events[s].append((key,var));events[f].append((key,None))
        times=sorted(events);active={}
        for s,f in zip(times,times[1:]):
            for key,var in events[s]:
                if var is None:active.pop(key,None)
                else:active[key]=var
            if not active:continue
            if charging:
                external=max((calendar.connections[e].get(t,0) for t in range(s,f,300)),default=0)
                remaining=calendar.plugs[e]-external
            else:
                remaining=calendar.physical[e]-int(np.max(calendar.presence[e][s-calendar.t0:f-calendar.t0]))
            # Cada bus solo puede ocupar un lugar a la vez por la construcción de sus huecos.
            if remaining<max_buses:
                model.addConstr(gp.quicksum(active.values())<=remaining)
                constraints+=1
    return constraints

def resolver_conjunto(sequences,chain,d,starts,calendar,tariffs,limit=2.,deadline=None):
    if not 1<=len(sequences)<=MAX_SECUENCIAS or any(not ts for ts in sequences):
        raise ValueError(f'Se requieren entre una y {MAX_SECUENCIAS} secuencias no vacías')
    if len({t['sector_id'] for ts in sequences for t in ts})!=1:
        raise ValueError('El grupo debe pertenecer al mismo sector')
    model=gp.Model('recargas_conjuntas');model.Params.OutputFlag=0
    model.Params.Threads=1;model.Params.TimeLimit=limit
    model.Params.FeasibilityTol=1e-8;model.Params.MIPGap=.02
    occupancy=defaultdict(list);connections=defaultdict(list)
    solutions=[];objective=gp.LinExpr();option_count=0
    def expired():return deadline is not None and time.perf_counter()>=deadline
    try:
        for b,trips in enumerate(sequences):
            if expired():return None,dict(estado='presupuesto')
            first='S:'+trips[0]['inicio_stop_id'];last='S:'+trips[-1]['fin_stop_id']
            initials=[t for t in starts if calendar.t0+d[t,first][1]<=trips[0]['inicio_s']]
            finals=[t for t in starts+sorted(calendar.physical)
                    if trips[-1]['fin_s']+d[last,t][1]<=calendar.horizon
                    and (t not in calendar.physical or calendar.libre(t,trips[-1]['fin_s']+d[last,t][1],calendar.horizon))]
            if not initials or not finals:return None,dict(estado='sin_terminal')
            x=model.addVars(initials,vtype='B',name=f'inicial_{b}')
            z=model.addVars(finals,vtype='B',name=f'final_{b}')
            energy=model.addVars(len(trips),lb=RESERVA,ub=BATERIA,name=f'energia_{b}')
            model.addConstr(x.sum()==1);model.addConstr(z.sum()==1)
            model.addConstr(energy[0]==BATERIA-1.4*(trips[0]['distancia_servicio_km']+gp.quicksum(d[t,first][0]*x[t] for t in initials)))
            model.addConstr(energy[len(trips)-1]-1.4*gp.quicksum(d[last,t][0]*z[t] for t in finals)>=RESERVA)
            objective+=.5*(gp.quicksum(d[t,first][0]*x[t] for t in initials)+gp.quicksum(d[last,t][0]*z[t] for t in finals))
            for t in finals:
                if t in calendar.physical:
                    occupancy[t].append((trips[-1]['fin_s']+d[last,t][1],calendar.horizon,z[t]))
            choices={}
            for j in range(1,len(trips)):
                if expired():return None,dict(estado='presupuesto')
                prev,trip=trips[j-1],trips[j]
                origin='S:'+prev['fin_stop_id'];target='S:'+trip['inicio_stop_id']
                km,dt=d[origin,target]
                if prev['fin_s']+dt>trip['inicio_s']:return None,dict(estado='enlace_temporal')
                opts=opciones(origin,target,prev['fin_s'],trip['inicio_s'],d,calendar,tariffs,interior=len(sequences)>=3)
                y=model.addVars(len(opts),vtype='B',name=f'visita_{b}_{j}')
                q=model.addVars(len(opts),lb=0,name=f'carga_{b}_{j}')
                model.addConstr(y.sum()<=1)
                for k,c in enumerate(opts):
                    model.addConstr(q[k]<=c['maxq']*y[k])
                    model.addGenConstrIndicator(y[k],True,energy[j-1]>=RESERVA+1.4*c['km1'])
                    model.addGenConstrIndicator(y[k],True,energy[j-1]-1.4*c['km1']+q[k]<=BATERIA)
                    occupancy[c['e']].append((c['start'],c['end'],y[k]))
                    connections[c['e']].append((c['start'],c['end'],y[k]))
                model.addConstr(energy[j]==energy[j-1]-1.4*(km+trip['distancia_servicio_km'])+
                                gp.quicksum(q[k]-1.4*(c['km1']+c['km2']-km)*y[k] for k,c in enumerate(opts)))
                objective+=.5*km+gp.quicksum((5+.5*(c['km1']+c['km2']-km))*y[k]+c['price']*q[k] for k,c in enumerate(opts))
                choices[j]=(opts,y,q);option_count+=len(opts)
            solutions.append((trips,initials,finals,x,z,choices))
        physical_constraints=acoplar(model,occupancy,calendar,max_buses=len(sequences))
        charging_constraints=acoplar(model,connections,calendar,True,max_buses=len(sequences))
        if expired():return None,dict(estado='presupuesto')
        if deadline is not None:model.Params.TimeLimit=min(limit,deadline-time.perf_counter())
        model.setObjective(objective);model.optimize()
        info=dict(estado=int(model.Status),incumbente=model.SolCount>0,opciones=option_count,
                  tiempo_solver_s=model.Runtime,restricciones_fisicas=physical_constraints,
                  restricciones_conexiones=charging_constraints)
        if not model.SolCount:return None,info
        result=[]
        for trips,initials,finals,x,z,choices in solutions:
            begin=next(t for t in initials if x[t].X>.5);final=next(t for t in finals if z[t].X>.5)
            charges={}
            for j,(opts,y,q) in choices.items():
                selected=next(((c,q[k].X) for k,c in enumerate(opts) if y[k].X>.5),None)
                if selected:charges[j]=selected
            result.append(armar_plan(trips,begin,final,charges,chain,calendar,d))
        return result,info
    finally:model.dispose()


def armar_plan(trips,begin,final,charges,chain,calendar,d):
    """Actividades de una jornada fija; charges[j]=(opción, kWh) es la recarga antes del servicio j."""
    acts=[];now=calendar.t0;loc=begin
    for j,trip in enumerate(trips):
        target='S:'+trip['inicio_stop_id'];selected=charges.get(j) if j else None
        if selected:
            c,amount=selected
            esperar(acts,loc,now,c['start']-c['dt1'])
            agregar_viaje(acts,loc,c['e'],c['start']-c['dt1'],d)
            blocks=(c['end']-c['start'])//300
            for s in range(c['start'],c['end'],300):
                acts.append(actividad('carga',c['e'],c['e'],s,s+300,q=max(0.,amount)/blocks))
            now=agregar_viaje(acts,c['e'],target,c['end'],d)
        else:
            departure=trip['inicio_s']-d[loc,target][1]
            esperar(acts,loc,now,departure)
            now=agregar_viaje(acts,loc,target,departure,d)
        esperar(acts,target,now,trip['inicio_s'])
        loc='S:'+trip['fin_stop_id'];now=trip['fin_s']
        acts.append(actividad('servicio',target,loc,trip['inicio_s'],now,trip['distancia_servicio_km'],trip=trip['corrida_id']))
    now=agregar_viaje(acts,loc,final,now,d);esperar(acts,final,now,calendar.horizon)
    return dict(bus_id='',cadena_fase2=chain,sector_id=trips[0]['sector_id'],terminal_inicial=begin,
                terminal_final=final,corridas=[t['corrida_id'] for t in trips],actividades=acts)
