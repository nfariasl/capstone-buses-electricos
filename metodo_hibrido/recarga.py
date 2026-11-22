"""Reoptimización local de recargas sobre servicios fijos, con reservas transaccionales."""
import math
import time
from collections import defaultdict
import gurobipy as gp
from metodo_hibrido.calendario import Calendario, actividad, agregar_viaje, esperar, precio
from metodo_hibrido.energia import BATERIA, RESERVA

def ocupaciones(plan):
    for a in plan['actividades']:
        if a['origen'].startswith('E') and a['tipo'] in ('espera', 'carga'):
            yield a['origen'], a['inicio_s'], a['fin_s'], a['tipo']=='carga'

def cambiar_reservas(calendar, plans, sign):
    for p in plans:
        for e, s, f, charging in ocupaciones(p):
            if sign == 1:
                calendar.reservar(e,s,f,charging)
            else:
                calendar.presence[e][s-calendar.t0:f-calendar.t0] -= 1
                if charging:
                    for t in range(s,f,300):
                        calendar.connections[e][t] -= 1

def opciones(origin, target, earliest, latest, d, calendar, tariffs,interior=False):
    result=[]
    for e in sorted(calendar.physical):
        km1,dt1=d[origin,e]; km2,dt2=d[e,target]
        first=math.ceil((earliest+dt1)/300)*300
        last=math.floor((latest-dt2)/300)*300
        runs=[]; run=[]
        for s in range(first,last,300):
            if calendar.libre(e,s,s+300,True):
                run.append(s)
            elif run:
                runs.append(run); run=[]
        if run:runs.append(run)
        for run in runs:
            lengths=sorted({min(len(run),n) for n in (1,2,3,4,6,8,12,16,21,24)})
            for n in lengths:
                # Ambos extremos y cambios tarifarios. Catálogo acotado, no exhaustivo.
                starts={run[0],run[-1]+300-n*300}
                if interior:starts.add(run[0]+((len(run)-n)//2)*300)
                starts.update(t for t in run if t+n*300<=run[-1]+300 and precio(t,tariffs)!=precio(t-300,tariffs))
                for s in sorted(starts):
                    f=s+n*300
                    result.append(dict(e=e,start=s,end=f,km1=km1,km2=km2,dt1=dt1,dt2=dt2,
                                       maxq=15*n,price=sum(precio(t,tariffs) for t in range(s,f,300))/n))
    return result

def resolver_jornada(trips, chain, d, starts, calendar, tariffs, limit=2., conservative=True,deadline=None):
    """MILP pequeño: una cadena fija, ninguna variable bus×servicio global."""
    model=gp.Model('reparacion_local'); model.Params.OutputFlag=0
    model.Params.Threads=1; model.Params.TimeLimit=limit
    model.Params.FeasibilityTol=1e-8
    model.Params.MIPGap=.02
    n=len(trips); energy=model.addVars(n,lb=RESERVA,ub=BATERIA,name='energia_fin')
    first='S:'+trips[0]['inicio_stop_id']; last='S:'+trips[-1]['fin_stop_id']
    initial=[t for t in starts if calendar.t0+d[t,first][1]<=trips[0]['inicio_s']]
    finals=[t for t in starts+sorted(calendar.physical) if trips[-1]['fin_s']+d[last,t][1]<=calendar.horizon
            and (t not in calendar.physical or calendar.libre(t,trips[-1]['fin_s']+d[last,t][1],calendar.horizon))]
    if not initial or not finals:model.dispose();return None,dict(estado='sin_terminal')
    x=model.addVars(initial,vtype='B',name='salida'); z=model.addVars(finals,vtype='B',name='retorno')
    model.addConstr(x.sum()==1);model.addConstr(z.sum()==1)
    model.addConstr(energy[0]==BATERIA-1.4*(gp.quicksum(d[t,first][0]*x[t] for t in initial)+trips[0]['distancia_servicio_km']))
    model.addConstr(energy[n-1]-1.4*gp.quicksum(d[last,t][0]*z[t] for t in finals)>=RESERVA)
    objective=.5*(gp.quicksum(d[t,first][0]*x[t] for t in initial)+gp.quicksum(d[last,t][0]*z[t] for t in finals))
    choices={}; count=0
    for j,trip in enumerate(trips):
        if deadline is not None and time.perf_counter()>=deadline:
            model.dispose();return None,dict(estado='presupuesto')
        if conservative:
            model.addConstr(energy[j]>=RESERVA+1.4*min(d['S:'+trip['fin_stop_id'],t][0] for t in starts))
        if j==0:continue
        prev=trips[j-1]; origin='S:'+prev['fin_stop_id'];target='S:'+trip['inicio_stop_id']
        km,dt=d[origin,target]
        if prev['fin_s']+dt>trip['inicio_s']:
            model.dispose();return None,dict(estado='enlace_temporal')
        opts=opciones(origin,target,prev['fin_s'],trip['inicio_s'],d,calendar,tariffs)
        y=model.addVars(len(opts),vtype='B',name=f'visita_{j}')
        q=model.addVars(len(opts),lb=0,name=f'carga_{j}')
        model.addConstr(y.sum()<=1)
        for k,c in enumerate(opts):
            model.addConstr(q[k]<=c['maxq']*y[k])
            model.addGenConstrIndicator(y[k],True,energy[j-1]>=RESERVA+1.4*c['km1'])
            model.addGenConstrIndicator(y[k],True,energy[j-1]-1.4*c['km1']+q[k]<=BATERIA)
        model.addConstr(energy[j]==energy[j-1]-1.4*(km+trip['distancia_servicio_km'])+
                        gp.quicksum(q[k]-1.4*(c['km1']+c['km2']-km)*y[k] for k,c in enumerate(opts)))
        objective+=.5*km+gp.quicksum((5+.5*(c['km1']+c['km2']-km))*y[k]+c['price']*q[k] for k,c in enumerate(opts))
        choices[j]=(opts,y,q);count+=len(opts)
    model.setObjective(objective)
    if deadline is not None:
        remaining=deadline-time.perf_counter()
        if remaining<=0:
            model.dispose();return None,dict(estado='presupuesto')
        model.Params.TimeLimit=min(limit,remaining)
    model.optimize()
    info=dict(estado=int(model.Status),opciones=count,tiempo_solver_s=model.Runtime,incumbente=model.SolCount>0)
    if not model.SolCount:model.dispose();return None,info
    begin=next(t for t in initial if x[t].X>.5);final=next(t for t in finals if z[t].X>.5)
    acts=[];now=calendar.t0;loc=begin
    for j,trip in enumerate(trips):
        target='S:'+trip['inicio_stop_id']
        selected=None
        if j:
            opts,y,q=choices[j]
            selected=next(((c,q[k].X) for k,c in enumerate(opts) if y[k].X>.5),None)
        if selected:
            c,amount=selected
            esperar(acts,loc,now,c['start']-c['dt1'])
            agregar_viaje(acts,loc,c['e'],c['start']-c['dt1'],d)
            blocks=(c['end']-c['start'])//300
            for t in range(c['start'],c['end'],300):
                acts.append(actividad('carga',c['e'],c['e'],t,t+300,q=max(0.,amount)/blocks))
            now=agregar_viaje(acts,c['e'],target,c['end'],d)
        else:
            departure=trip['inicio_s']-d[loc,target][1]
            esperar(acts,loc,now,departure)
            now=agregar_viaje(acts,loc,target,departure,d)
        esperar(acts,target,now,trip['inicio_s'])
        loc='S:'+trip['fin_stop_id'];now=trip['fin_s']
        acts.append(actividad('servicio',target,loc,trip['inicio_s'],now,trip['distancia_servicio_km'],trip=trip['corrida_id']))
    now=agregar_viaje(acts,loc,final,now,d);esperar(acts,final,now,calendar.horizon)
    plan=dict(bus_id='',cadena_fase2=chain,sector_id=trips[0]['sector_id'],terminal_inicial=begin,
              terminal_final=final,corridas=[t['corrida_id'] for t in trips],actividades=acts)
    model.dispose()
    return plan,info

def costo(plans,tariffs):
    value=250*len(plans)
    for p in plans:
        prev=None
        for a in p['actividades']:
            value+=.5*a['distancia_km']
            if a['tipo']=='carga':
                value+=a['carga_kwh']*precio(a['inicio_s'],tariffs)
                if prev is None or prev['tipo']!='carga' or prev['destino']!=a['origen'] or prev['fin_s']!=a['inicio_s']:value+=5
            prev=a
    return value
