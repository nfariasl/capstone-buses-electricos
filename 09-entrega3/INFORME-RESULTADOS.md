# Informe de resultados · Entrega 3

Grupo 29 · ICS2122 · Planificación de la operación de buses eléctricos en la RM
Escrito el 22-nov-2026 para que todo el grupo entienda qué resultados tenemos, qué significan y de dónde sale cada cifra.

## 1. En una página

- **Lo que hacemos:** decidir cuántos buses eléctricos hacen falta y cómo se reparten las 64.502 corridas de las 417 rutas, de modo que el costo del día sea mínimo y ningún bus se quede sin batería.
- **Resultado principal (día laboral):** **7.351 buses y USD 2.617.469 al día**, con el método de *cuartetos al azar* (promedio de 3 semillas, 40 min de búsqueda).
- **Contra el caso base** (cada ruta se planifica por separado, sin compartir buses entre rutas): **−1.333 buses (−15,4 %) y −USD 445.248 (−14,5 %)** en el día laboral.
- **En la semana** (5 días laborales + sábado + domingo): USD 16,27 millones contra USD 19,12 millones del caso base, **−14,9 %** (USD 2,85 millones menos).
- **Qué tan cerca del óptimo estamos:** en los 5 casos chicos donde pudimos demostrar el óptimo, el método queda a **0,13 % en promedio** (peor caso 0,31 %).
- **Dónde nos faltan datos:** la sensibilidad todavía no tiene resultados en el repositorio, y la repetibilidad del día siguiente es un límite conocido (sección 8).

## 2. Qué es cada cosa (glosario rápido)

| Término | Qué significa |
|---|---|
| **Corrida** | Un viaje programado de una ruta, con hora de salida y de llegada. Hay 64.502 en un día laboral. |
| **Caso base** | Política simple de comparación: cada ruta usa sus propios buses y recarga por su cuenta (política «miope»). Día laboral: 8.684 buses y USD 3.062.717. |
| **Plan inicial** | El plan que arma nuestro método antes de mejorarlo (construcción cronológica). Día laboral: 7.570 buses y USD 2.677.608. **No es el caso base**; es el punto de partida de la mejora. |
| **Cuarteto** | Grupo de 4 buses cuyas corridas se reparten de nuevo entre ellos, junto con sus recargas, buscando un plan más barato. «Al azar» = los 4 buses se eligen al azar con una semilla; «parecidos» = se eligen buses con horarios parecidos. |
| **Exacta** | Modelo MILP que, en casos chicos, encuentra el plan óptimo demostrado. Sirve como vara para medir a las heurísticas. |
| **Brecha** | Cuánto más caro es un plan que el óptimo (o que la mejor cota conocida), en %. |
| **Cota** | Piso que ningún plan puede romper. Día laboral: 6.601 buses simultáneos a las 08:00 más los km de servicio dan USD 2.322.956. |

Costos del modelo: USD 250 por bus, USD 0,5 por km, energía entre USD 0,10 y 0,22 por kWh según la hora y USD 5 por sesión de carga. Los buses pesan cerca del 70 % del costo, por eso el método ataca primero el número de buses.

## 3. Resultado principal: red completa

### 3.1 Los tres tipos de día

| Día | Corridas | Caso base | Cuartetos al azar (40 min) | Diferencia |
|---|---|---|---|---|
| Laboral | 64.502 | 8.684 buses · USD 3.062.717 | **7.351 buses · USD 2.617.469** | −15,4 % buses · −14,5 % costo |
| Sábado | 43.619 | 5.492 buses · USD 2.040.216 | **4.517 buses · USD 1.704.045** | −17,8 % buses · −16,5 % costo |
| Domingo | 37.377 | 4.669 buses · USD 1.765.184 | **3.899 buses · USD 1.474.580** | −16,5 % buses · −16,5 % costo |
| **Semana** | | USD 19.118.985 | **USD 16.265.970** | **−14,9 % costo** |

- Costo semanal = 5 × laboral + sábado + domingo.
- La flota que hay que tener es la del día laboral: 7.351 buses.
- Cada cifra de cuartetos es el promedio de 3 semillas.

### 3.2 Cuánto aporta cada paso (día laboral)

| Paso | Buses | Costo (USD) |
|---|---|---|
| Caso base (política miope) | 8.684 | 3.062.717 |
| Plan inicial del método | 7.570 | 2.677.608 |
| Mejora por pares y tríos (40 min) | 7.433 | 2.639.411 |
| **Mejora por cuartetos al azar (40 min)** | **7.351** | **2.617.469** |

La construcción ya ahorra más que la mejora local; los cuartetos le sacan 2,25 % extra al plan inicial (−219 buses). Sábado: −4,80 %; domingo: −8,00 % contra el plan inicial.

## 4. Qué método gana y por qué

Se probaron todos los tamaños de grupo (pares, tríos, cuartetos, quintetos, octetos), con selección «parecidos» o «azar», y una mezcla creciente. Día laboral, 40 min:

| Método | Buses | Costo (USD) |
|---|---|---|
| Pares | 7.524 | 2.657.890 |
| Pares + tríos | 7.433 | 2.639.411 |
| Tríos al azar | 7.374 | 2.622.455 |
| **Cuartetos al azar** | **7.351** | **2.617.469** |
| Quintetos al azar | 7.369 | 2.627.932 |
| Octetos al azar | 7.489 | 2.658.096 |
| Mezcla creciente (al azar) | 7.520 | 2.656.563 |

Lo que se ve:
- Elegir los buses **al azar** le gana a elegirlos «parecidos» (cuartetos parecidos se estancan en 7.496). Los grupos parecidos se atascan en un óptimo local.
- Hay un punto dulce en el tamaño del grupo: **4**. Los grupos de 8 (octetos) quedan peores en el mismo tiempo.
- La regla del grupo fue elegir el más barato con el mismo tiempo, sin umbral de mejora mínima.
- Las corridas se guardan en `octetos/resultados/red_completa_417_{L,S,D}.csv` (67 filas el día laboral, 0 errores).

## 5. Qué tan cerca del óptimo estamos

Los 5 casos chicos (2 a 4 rutas, 84 a 157 corridas) se resolvieron con el modelo exacto: **óptimo demostrado en los 5, en 1 a 8 minutos cada uno**. Con eso se mide la brecha de cada heurística (120 s de búsqueda, 5 casos, sin recarga forzada):

| Método | Brecha media al óptimo | Peor caso |
|---|---|---|
| Pares | 1,24 % | 3,39 % |
| Pares + tríos | 0,61 % | 2,70 % |
| Mezcla creciente | 0,56 % | 2,70 % |
| Tríos al azar | 0,15 % | 0,38 % |
| Quintetos al azar | 0,14 % | 0,32 % |
| Octetos al azar | 0,14 % | 0,38 % |
| **Cuartetos al azar** | **0,13 %** | **0,31 %** |

Casos más grandes resueltos al óptimo con la exacta podada:

| Caso | Corridas | Buses | Costo exacto (USD) | Cuartetos (5 min) |
|---|---|---|---|---|
| rutas_06 | 129 | 24 | 7.506,30 | — |
| rutas_08 | 200 | 38 | 11.517,04 | — |
| mediano_200 | 200 | 24 | 8.177,94 | +0,03 % |
| **rutas_10** | **293** | **60** | **18.204,24** | **+0,57 %** |

**Lectura:** donde se puede demostrar el óptimo, el método queda a menos de 1 % de él. En la red completa no se puede demostrar el óptimo; ahí la referencia es la cota de la sección 2 (brecha de 12,7 % en el día laboral). Esa cota es débil: ignora la recarga, los sectores y el espacio de los electroterminales, así que la brecha real es menor.

## 6. Recarga forzada: ¿y si la batería es más chica?

El profesor pidió ver qué pasa cuando los buses *tienen que* recargar. Los casos originales (batería de 350 kWh) casi no recargan. Se hicieron copias con **150 kWh** y **120 kWh** (con 100 kWh no alcanza: hay servicios que necesitan entre 105 y 112 kWh).

Mejor heurística (cuartetos o pares + tríos) contra el caso inicial de cada caso:

| Batería | Mejora contra el plan inicial (rango en 5 casos) |
|---|---|
| 150 kWh | −6 % a −27 % |
| 120 kWh | −14 % a −24 % |

Distancia de la mejor heurística al mejor plan de la exacta (la exacta **no cierra en 15 min** con recarga, así que su valor es una cota superior del óptimo):

| Caso | Heurística vs exacta |
|---|---|
| bat150, 5 casos chicos | +0,9 % a +6,8 % |
| bat120, 5 casos chicos | 0,0 % a +6,6 % |
| bat150_rutas_10 (293 corridas) | **−0,4 %** (la heurística le gana a la exacta en 1 h) |

Lo que se ve:
- Con recarga, la exacta deja de cerrar: las cotas dejan brechas de 2 % a 18 % contra su mejor plan. Por eso la distancia de las heurísticas **no es una brecha al óptimo**, solo contra el mejor plan que la exacta encontró.
- Más tiempo de búsqueda casi no ayuda: cuartetos con 15 min queda casi igual que con 2 min. La búsqueda se detiene por «sin mejoras en el vecindario», no por falta de tiempo.
- En el caso más grande (rutas_10 con 150 kWh) los cuartetos (62 buses, USD 19.625) le ganan a la exacta tras 1 h con 2 hilos (64 buses, USD 19.697), y el plan inicial queda en 77 buses y USD 23.283.

## 7. Qué dicen los KPI

Los KPI de Gustavo (`kpi/`) se recalcularon el 22-nov sobre el **plan final: cuartetos al azar, semilla 1, 40 min** (7.351 buses en día laboral, 4.521 el sábado y 3.902 el domingo). Ya no hay cifras del plan de 7.427 de octubre en `kpi/resultados/`. Los hallazgos:

| Día | Buses (base → cuartetos) | Δ buses | Costo USD/día (base → cuartetos) | Δ costo |
|---|---|---|---|---|
| Laboral | 8.684 → 7.351 | −15,4 % | 3.062.717 → 2.617.245 | −14,5 % |
| Sábado | 5.492 → 4.521 | −17,7 % | 2.040.216 → 1.704.731 | −16,4 % |
| Domingo | 4.669 → 3.902 | −16,4 % | 1.765.184 → 1.475.231 | −16,4 % |

- **Km en vacío** (día laboral): bajan 30,4 % contra el caso base.
- **Los cargadores no son el cuello de botella.** En día laboral el pico es de 15 a 38 buses cargando a la vez por electroterminal (11 a 21 % de las conexiones), entre las 19:25 y las 19:55. Ojo: eso cae al inicio del tramo caro (19:00 a 22:00), a diferencia del plan de octubre. El sábado llega a 41 % (La Reina) a las 17:25. El caso base llena las conexiones de E2, E4 y E5 entre las 20:00 y las 22:00.
- **Las plazas se llenan solo al cierre.** Durante la operación, la ocupación máxima es de 11 a 21 % de las plazas en día laboral (hasta 41 % el sábado). Al cierre, exactamente 700 buses quedan estacionados en los electroterminales (la capacidad total) y las plazas pasan entre 75 y 155 min al 100 % después de medianoche. En el caso base, ninguno termina en un electroterminal. Fuente: `kpi/resultados/plazas_metodo_{L,S,D}_resumen.csv`.
- **Desbalance entre sectores.** El sector 3 (Los Espinos) carga solo 37,6 % de su energía en su propio electroterminal (36,5 % en E2 y 18,7 % en E5); los demás cargan entre 56,5 % y 76,1 % en el suyo.
- **La energía casi no pesa:** 0,4 % del costo en día laboral. Se carga el 2,5 % de la energía consumida, porque los buses parten llenos y terminan con 66 kWh en promedio.

## 8. Límites que hay que decir en voz alta

1. **El día siguiente no se repite solo.** Para volver a partir con batería llena habría que reponer 2,08 GWh de noche (plan de cuartetos). Con las 700 conexiones a 180 kW tomaría 16,5 h el día laboral (10,7 h el sábado, 9,1 h el domingo), y 6.651 de los 7.351 buses terminan en terminales sin cargadores. Por electroterminal (`kpi/resultados/repetibilidad.md`), en la ventana nocturna mediana de 7,5 h las 700 conexiones entregan solo el 45 % de esa energía: harían falta 278 MW (hay 126) o 1.547 conexiones. El sábado se cubre el 75 % y el domingo el 90 %. El caso base tampoco se repite (52 % en día laboral). El equipo docente ya lo preguntó el 8-oct.
2. **No hay prueba de optimalidad en la red completa.** Solo en casos de hasta 293 corridas.
3. **Los límites eléctricos son supuestos.** `transformer_mw` no viene en los datos; se modeló como conexiones × 180 kW.
4. **El costo de espera (0,03 USD/min) no se cobra** en los planes.
5. **La sensibilidad no está terminada.** `sensibilidad/` tiene los escenarios definidos (plazas −20 %, +20 %, +50 %, mitad de cargadores, cierre de cada electroterminal, tarifa de punta +50 %, plazas por demanda), pero aún no hay resultados en el repositorio. Falta variar consumo, batería y costos, que hoy están fijos en el código.
6. **Los resultados de cuartetos son promedio de 3 semillas.** El plan individual que se audita corresponde a una semilla; hay que decidir cuál usar para los KPI.

## 9. Dónde está cada cosa

| Qué | Dónde |
|---|---|
| Resultados red completa (L, S, D) | `09-entrega3/octetos/resultados/red_completa_417_{L,S,D}.csv` |
| Casos chicos: heurísticas y exacta | `casos_chicos.csv`, `casos_chicos_exacta.csv` |
| Casos con recarga forzada | `recarga_bat150*.csv`, `recarga_bat120*.csv` |
| Detalle de la cola nocturna del 22-nov | `09-entrega3/octetos/INFORME-COLA-NOCTURNA.md` |
| Casos medianos y de 10 rutas | `casos_rutas*.csv`, `casos_medianos_exacta_podada.csv` |
| KPI y uso de electroterminales | `09-entrega3/kpi/` (`resultados/kpi_planes.md`) |
| Escenarios de sensibilidad | `09-entrega3/sensibilidad/` |
| Plan de trabajo y rúbrica | `09-entrega3/PLAN-ENTREGA3.md` |
| Auditoría de las láminas y reparto 12–20 | `09-entrega3/presentacion/` |

Los planes de cada corrida (`planes_417_*`) no están en GitHub, solo en el computador donde se corrió.

## 10. Para reproducir

Con Gurobi instalado y la licencia académica:

```bash
bash 09-entrega3/octetos/correr_todo.sh
python3 09-entrega3/kpi/kpi_planes.py
python3 -m pytest -q 09-entrega3/kpi/
```

Cada corrida deja una fila en un CSV y se puede retomar con `--continuar`.
