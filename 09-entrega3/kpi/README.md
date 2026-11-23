# KPI y uso de electroterminales

Scripts para calcular todos los KPI de cada plan y el uso de los cargadores de cada electroterminal
durante el día, para el caso base y el método, en día laboral, sábado y domingo. Responden a lo que
pidió el profesor en la reunión del 17-nov: calcular todos los KPI y revisar la ocupación de cada
electroterminal a lo largo del día.

No dependen de la elección de cuartetos, octetos u otra agrupación: leen planes ya resueltos y
auditados. Para el plan final, basta agregar su carpeta en `PLANES` de `planes.py`.

## Uso

Desde la raíz del repositorio (solo necesita pandas y matplotlib, sin Gurobi):

```bash
python3 09-entrega3/kpi/kpi_planes.py
python3 09-entrega3/kpi/uso_electroterminales.py
python3 -m pytest -q 09-entrega3/kpi/
```

La ocupación de plazas necesita `actividades.csv`, que no está en GitHub pero sí en las carpetas de
planes del computador donde se corrió el método (una vez por día):

```bash
python3 09-entrega3/kpi/ocupacion_plazas.py --plan 09-entrega3/octetos/resultados/planes_417_L/instancia_417_cuartetos_azar_s1_2400s --nombre metodo_L
python3 09-entrega3/kpi/ocupacion_plazas.py --plan 09-entrega3/octetos/resultados/planes_417_S/instancia_417_S_cuartetos_azar_s1_2400s --nombre metodo_S
python3 09-entrega3/kpi/ocupacion_plazas.py --plan 09-entrega3/octetos/resultados/planes_417_D/instancia_417_D_cuartetos_azar_s1_2400s --nombre metodo_D
```

El script comprueba que su pico coincida con la `ocupacion_maxima` del auditor.

## Archivos

| Archivo | Qué hace |
|---|---|
| `planes.py` | Lista de planes, lectura de `resumen.json`, `jornadas.csv` y `recargas.csv`, y validación de que los tres cuadren |
| `kpi_planes.py` | 30 KPI por plan, ahorro del método contra el caso base y tabla por sector |
| `uso_electroterminales.py` | Perfil de carga por electroterminal en bloques de 5 min, resumen, matriz sector × electroterminal y figuras |
| `ocupacion_plazas.py` | Ocupación de plazas por electroterminal cada 5 min desde `actividades.csv`, separando buses cargando, esperando durante la operación y estacionados al cierre |
| `repetibilidad.py` | Por electroterminal: energía a reponer de noche, lo que alcanzan a entregar sus conexiones en la ventana nocturna, y cuántos MW y conexiones faltan para repetir el día (necesita `actividades.csv`; supuestos en su encabezado) |
| `test_kpi.py`, `test_ocupacion_plazas.py`, `test_repetibilidad.py` | Pruebas con planes chicos y con los planes del repositorio |
| `resultados/` | Salidas: CSV, `kpi_planes.md`, `plazas_metodo_{L,S,D}_*` y figuras PNG |

## Controles

- Antes de usar un plan se comprueba que `jornadas.csv`, `recargas.csv` y `resumen.json` den los mismos
  buses, corridas, km, energía, sesiones y costo. Los seis planes cuadran.
- El pico de buses cargando a la vez y el de plazas ocupadas en cada electroterminal coinciden con los
  que reportó el auditor en `resumen.json` (`cargas_simultaneas_maximas` y `ocupacion_maxima`).

## Planes usados (desde el 22-nov)

| Plan | Carpeta |
|---|---|
| Caso base L, S, D | `codigo/output/tres_fases/red_417_{L,S,D}_caso_base/` |
| Método L, S, D | `09-entrega3/octetos/resultados/planes_417_{L,S,D}/instancia_417{,_S,_D}_cuartetos_azar_s1_2400s/` |

El método es el plan final de la Entrega 3: cuartetos al azar, semilla 1, 40 min (7.351 / 4.521 / 3.902
buses). Esas carpetas no están en GitHub: solo existen en el Mac donde se corrieron. Hasta el 22-nov,
`kpi/` usaba los planes de octubre (7.427 buses en día laboral); esas cifras ya no van.

## Hallazgos

| Día | Buses (base → método) | Δ buses | Costo USD/día (base → método) | Δ costo |
|---|---|---|---|---|
| Laboral | 8.684 → 7.351 | −15,4 % | 3.062.717 → 2.617.245 | −14,5 % |
| Sábado | 5.492 → 4.521 | −17,7 % | 2.040.216 → 1.704.731 | −16,4 % |
| Domingo | 4.669 → 3.902 | −16,4 % | 1.765.184 → 1.475.231 | −16,4 % |

- **Los cargadores no son el cuello de botella del método.** En día laboral el pico es de 15 a 38 buses
  cargando a la vez por electroterminal (11 a 21 % de las conexiones), entre las 19:25 y las 19:55, al
  inicio del tramo caro de 19:00 a 22:00. El sábado llega a 41 % (La Reina, 17:25). El caso base, que
  recarga al 100 %, llena las conexiones de E2, E4 y E5 entre las 20:00 y las 22:00.
- **Las plazas se llenan solo al cierre.** Durante la operación se ocupa como máximo el 11 a 21 % de las
  plazas en día laboral (22 a 41 % el sábado, 20 a 31 % el domingo). Al cierre, exactamente 700 buses
  quedan estacionados en los electroterminales, que es la capacidad total, y las plazas pasan entre 75 y
  155 min al 100 % después de medianoche. En el caso base ningún bus termina en un electroterminal.
- **Desbalance entre sectores.** El sector 3 (Los Espinos) carga solo el 37,6 % de su energía en su
  propio electroterminal, el 36,5 % en E2 El Conquistador y el 18,7 % en E5 Santa Rosa. Los demás
  sectores cargan entre 56,5 % y 76,1 % en el suyo.
- **La energía casi no pesa en el método:** 0,4 % del costo en día laboral. Se carga el 2,5 % de la
  energía consumida, porque los buses parten llenos y terminan con 66 kWh en promedio. Para repetir el
  día habría que reponer 2,08 GWh de noche.
