"""Genera las figuras del informe final (PDF vectorial) desde las instancias y salidas/para_figuras.json.

Paleta categórica validada (azul, naranja, aqua) con el validador del skill de visualización: el plan del
método siempre es azul y el caso base siempre es naranja, en todas las figuras.
"""
import json
import sys
from collections import defaultdict

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt  # noqa: E402

import fuentes  # noqa: E402

AQUI = fuentes.INFORME
PLAN, BASE, TERCERO = '#2a78d6', '#eb6834', '#1baf7a'
TINTA, TINTA_2, GRILLA = '#0b0b0b', '#52514e', '#e4e3df'
ANCHO = 6.2
TARIFA_PUNTA = 0.22
plt.rcParams.update({
    'font.family': 'serif', 'font.serif': ['Times New Roman', 'Times', 'STIXGeneral'],
    'mathtext.fontset': 'stix', 'font.size': 9, 'axes.edgecolor': TINTA_2, 'axes.labelcolor': TINTA,
    'xtick.color': TINTA_2, 'ytick.color': TINTA_2, 'axes.spines.top': False, 'axes.spines.right': False,
    'axes.grid': True, 'grid.color': GRILLA, 'grid.linewidth': .6, 'axes.axisbelow': True,
    'legend.frameon': False, 'pdf.fonttype': 42,
})


def miles(x, _=None):
    return f'{x:,.0f}'.replace(',', '.')


def coma(x, decimales=1):
    return f'{x:.{decimales}f}'.replace('.', ',')


def guardar(fig, nombre):
    fig.tight_layout()
    fig.savefig(AQUI / 'figures' / f'{nombre}.pdf')
    plt.close(fig)


def eje_horas(ax, desde=4, hasta=26):
    ax.set_xlim(desde, hasta)
    ax.set_xticks(range(desde, hasta + 1, 2), [f'{h % 24:02d}' for h in range(desde, hasta + 1, 2)])


def fig_corridas_dia():
    fig, ax = plt.subplots(figsize=(ANCHO, 2.7))
    for dia, etiqueta, color in (('L', 'Laboral', PLAN), ('S', 'Sábado', BASE), ('D', 'Domingo', TERCERO)):
        corridas = fuentes.leer_csv(fuentes.INSTANCIAS[dia] / 'corridas.csv')
        cambios = defaultdict(int)
        for c in corridas:
            cambios[int(c['inicio_s']) // 300] += 1
            cambios[int(c['fin_s']) // 300 + 1] -= 1
        x, y, activos = [], [], 0
        for b in range(min(cambios), max(cambios) + 1):
            activos += cambios.get(b, 0)
            x.append(b * 300 / 3600)
            y.append(activos)
        ax.plot(x, y, color=color, lw=1.6, label=etiqueta)
    eje_horas(ax)
    ax.set_xlabel('Hora del día')
    ax.set_ylabel('Corridas en curso (bloques de 5 min)')
    ax.yaxis.set_major_formatter(miles)
    ax.legend(loc='upper right', ncols=3)
    guardar(fig, 'corridas_dia')


def fig_ahorro_componentes(d):
    nombres = {'Flota': 'Buses', 'Km': 'Kilómetros', 'Energia': 'Energía', 'Sesiones': 'Sesiones de carga'}
    comp = d['componentes']
    total = sum(comp.values())
    claves = list(nombres)[::-1]
    valores = [comp[k] / 1000 for k in claves]
    fig, ax = plt.subplots(figsize=(ANCHO, 1.9))
    ax.barh([nombres[k] for k in claves], valores, color=PLAN, height=.55)
    for i, v in enumerate(valores):
        ax.text(v + 4, i, f'USD {miles(v * 1000)} ({coma(100 * v * 1000 / total)} %)', va='center', fontsize=8,
                color=TINTA)
    ax.set_xlim(0, max(valores) * 1.45)
    ax.set_xlabel('Ahorro contra el caso base (miles de USD por día laboral)')
    ax.grid(axis='y', visible=False)
    guardar(fig, 'ahorro_componentes')


def fig_tamano_grupo(d):
    datos = d['metodos_presupuesto']
    tam = {'trios|azar': 3, 'cuartetos|azar': 4, 'quintetos|azar': 5, 'octetos|azar': 8}
    orden = sorted(tam, key=tam.get)
    fig, ax = plt.subplots(figsize=(ANCHO, 2.6))
    for p, color, etiqueta in (('600.0', TERCERO, '10 min'), ('1200.0', BASE, '20 min'), ('2400.0', PLAN, '40 min')):
        ax.plot([tam[k] for k in orden], [datos[k][p] for k in orden], marker='o', ms=5, lw=1.6, color=color,
                label=etiqueta)
    ref = datos['pares_trios|']['2400.0']
    ax.axhline(ref, color=TINTA_2, lw=1, ls='--')
    ax.text(3.0, ref + 4, f'Pares + tríos con 40 min: {miles(ref)}', ha='left', fontsize=8, color=TINTA_2)
    ax.set_xticks([3, 4, 5, 8], ['3 (tríos)', '4 (cuartetos)', '5 (quintetos)', '8 (octetos)'])
    ax.set_xlabel('Buses por grupo, elegidos al azar')
    ax.set_ylabel('Buses del plan (día laboral)')
    ax.yaxis.set_major_formatter(miles)
    ax.legend(title='Tiempo de búsqueda', loc='lower right')
    guardar(fig, 'tamano_grupo')


def fig_energia_hora(d):
    eh = d['energia_hora']
    tarifas = json.loads(fuentes.leer_texto(fuentes.INSTANCIAS['L'] / 'escenario.json'))['tarifas']
    fig, ax = plt.subplots(figsize=(ANCHO, 2.6))
    for a, b, p in tarifas:
        if p >= TARIFA_PUNTA:
            ax.axvspan(a - .5, b - .5, color=GRILLA, alpha=.8, lw=0)
    horas = range(24)
    ax.bar([h - .2 for h in horas], eh['Base'], width=.38, color=BASE, label='Caso base')
    ax.bar([h + .2 for h in horas], eh['Plan'], width=.38, color=PLAN, label='Cuartetos al azar')
    techo = max(max(eh['Base']), max(eh['Plan'])) * 1.18
    ax.set_ylim(0, techo)
    for a, b, p in tarifas:
        if p >= TARIFA_PUNTA:
            ax.text((a + b) / 2 - .5, techo * .95, 'USD 0,22/kWh', ha='center', fontsize=8, color=TINTA_2)
    ax.set_xticks(range(0, 24, 2), [f'{h:02d}' for h in range(0, 24, 2)])
    ax.set_xlim(-.7, 23.7)
    ax.set_xlabel('Hora de la carga (día laboral); en gris, los tramos de tarifa más alta')
    ax.set_ylabel('% de la energía cargada')
    ax.legend(loc='upper left')
    guardar(fig, 'energia_hora')


def fig_uso_electroterminales():
    perfil = fuentes.leer_csv(fuentes.KPI / 'uso_e_perfil.csv')
    fig, ax = plt.subplots(figsize=(ANCHO, 2.5))
    for plan, color, etiqueta in (('caso_base_L', BASE, 'Caso base'), ('metodo_L', PLAN, 'Cuartetos al azar')):
        suma = defaultdict(int)
        for r in perfil:
            if r['plan'] == plan:
                suma[int(r['bloque_s'])] += int(r['buses_cargando'])
        xs = sorted(suma)
        ax.plot([x / 3600 for x in xs], [suma[x] for x in xs], color=color, lw=1.5, label=etiqueta)
    ax.axhline(700, color=TINTA_2, lw=1, ls='--')
    ax.text(4.2, 715, '700 conexiones en total', fontsize=8, color=TINTA_2)
    eje_horas(ax)
    ax.set_ylim(0, 800)
    ax.set_xlabel('Hora del día (laboral)')
    ax.set_ylabel('Buses cargando a la vez\n(suma de los cinco E)')
    ax.legend(loc='center left')
    guardar(fig, 'uso_electroterminales')


def fig_sensibilidad(d):
    filas = d['sens'][::-1]
    fig, ax = plt.subplots(figsize=(ANCHO, 3.1))
    ys = list(range(len(filas)))
    ax.axvspan(-.15, .15, color=GRILLA, alpha=.9, lw=0)
    ax.barh(ys, [f[1] for f in filas], color=PLAN, height=.5, label='Cuartetos al azar (20 min, semilla 1)')
    ax.scatter([f[2] for f in filas], ys, color=BASE, s=24, zorder=3, label='Plan inicial (determinista)')
    ax.set_yticks(ys, [f[0].replace('$-$', '−').replace('\\,\\%', ' %') for f in filas])
    ax.axvline(0, color=TINTA_2, lw=.8)
    ax.text(0, len(filas) - .4, 'banda de ruido', ha='center', fontsize=7.5, color=TINTA_2)
    ax.set_xlabel('Cambio del costo diario contra la base de la misma tanda (%)')
    ax.grid(axis='y', visible=False)
    ax.legend(loc='lower right')
    guardar(fig, 'sensibilidad')


def fig_atrasos(d):
    at = {int(k): v for k, v in d['atrasos'].items()}
    cvs = sorted(at)
    fig, ax = plt.subplots(figsize=(ANCHO, 2.4))
    ax.plot(cvs, [at[c][0] for c in cvs], marker='o', ms=5, lw=1.6, color=BASE, label='Caso base')
    ax.plot(cvs, [at[c][1] for c in cvs], marker='o', ms=5, lw=1.6, color=PLAN, label='Cuartetos al azar')
    for c in cvs:
        for v in at[c]:
            ax.annotate(f'{coma(v)} %', (c, v), xytext=(6, -3), textcoords='offset points', fontsize=8, color=TINTA)
    ax.set_xticks(cvs, [f'{c} %' for c in cvs])
    ax.set_xlim(8, 33)
    ax.set_xlabel('Variabilidad de los tiempos de viaje (coeficiente de variación)')
    ax.set_ylabel('Corridas con más de\n5 min de atraso (%)')
    ax.legend(loc='upper left')
    guardar(fig, 'atrasos')


def _gantt(ax, filas, titulo):
    """filas: lista de (etiqueta, [(inicio, fin, tipo)]) con tipo 'r' receptor, 'd' donante, 'c' carga."""
    colores = {'r': '#9ec3ef', 'd': BASE, 'c': TERCERO}
    for y, (etiqueta, bloques) in enumerate(filas[::-1]):
        ax.axhline(y, color=GRILLA, lw=.8, zorder=0)
        for a, b, tipo in bloques:
            ax.barh(y, b - a, left=a, height=.55, color=colores[tipo], edgecolor='white', lw=1)
    ax.set_yticks(range(len(filas)), [f[0] for f in filas[::-1]])
    ax.set_xlim(6, 22)
    ax.set_xticks(range(6, 23, 4), [f'{h:02d}' for h in range(6, 23, 4)])
    ax.set_title(titulo, fontsize=9, loc='left', color=TINTA)
    ax.grid(False)
    ax.spines['left'].set_visible(False)
    ax.tick_params(axis='y', length=0)


def fig_operaciones():
    r1 = [(6.0, 7.5, 'r'), (9.6, 11.2, 'r'), (15, 16.5, 'r'), (19, 20.5, 'r')]
    r2 = [(6.5, 8.0, 'r'), (12.5, 14, 'r'), (17, 18.6, 'r'), (20.3, 21.6, 'r')]
    r3 = [(7.0, 9.0, 'r'), (11, 12.5, 'r'), (14.5, 16, 'r'), (20.1, 21.5, 'r')]
    d = [(7.8, 9.3, 'd'), (10.2, 11.8, 'd'), (16.4, 18.0, 'd')]
    antes = [('Bus 1', r1), ('Bus 2', r2), ('Bus 3', r3), ('Bus 4', d)]
    despues = [('Bus 1', r1 + [d[0]]), ('Bus 2', r2 + [d[1]]), ('Bus 3', r3 + [d[2], (18.2, 19.6, 'c')]), ('Bus 4', [])]
    ra = [(6.0, 7.5, 'r'), (9.5, 11.0, 'r'), (14, 15.5, 'd'), (17.5, 19, 'd')]
    rb = [(6.5, 8.0, 'r'), (10, 11.5, 'r'), (14.5, 16, 'd'), (18, 19.5, 'd')]
    rot_antes = [('Bus 1', ra), ('Bus 2', rb)]
    rot_despues = [('Bus 1', ra[:2] + [(14.5, 16, 'd'), (18, 19.5, 'd')]), ('Bus 2', rb[:2] + [(14, 15.5, 'd'), (17.5, 19, 'd')])]
    fig, ejes = plt.subplots(2, 2, figsize=(ANCHO, 4.3), gridspec_kw=dict(height_ratios=[4, 2.2]))
    _gantt(ejes[0, 0], antes, 'Absorción, antes (4 buses)')
    _gantt(ejes[0, 1], despues, 'Absorción, después (3 buses)')
    ejes[0, 1].text(14, 0, 'bus eliminado', ha='center', va='center', fontsize=8, color=BASE)
    _gantt(ejes[1, 0], rot_antes, 'Rotación, antes')
    _gantt(ejes[1, 1], rot_despues, 'Rotación, después')
    ejes[1, 0].axvline(13, color=TINTA_2, lw=1, ls='--')
    ejes[1, 1].axvline(13, color=TINTA_2, lw=1, ls='--')
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(color='#9ec3ef', label='Corrida que se queda en su bus'),
                        Patch(color=BASE, label='Corrida que cambia de bus'),
                        Patch(color=TERCERO, label='Recarga en electroterminal')],
               loc='lower center', ncols=3, fontsize=8)
    fig.tight_layout(rect=(0, .07, 1, 1))
    fig.savefig(AQUI / 'figures' / 'operaciones.pdf')
    plt.close(fig)


def main():
    d = json.loads((AQUI / 'salidas/para_figuras.json').read_text(encoding='utf-8'))
    (AQUI / 'figures').mkdir(exist_ok=True)
    fig_corridas_dia()
    fig_ahorro_componentes(d)
    fig_tamano_grupo(d)
    fig_energia_hora(d)
    fig_uso_electroterminales()
    fig_sensibilidad(d)
    fig_atrasos(d)
    fig_operaciones()
    print('8 figuras en figures/')
    return 0


if __name__ == '__main__':
    sys.exit(main())
