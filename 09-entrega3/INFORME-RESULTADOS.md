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

Los KPI de Gustavo (`kpi/`) se calcularon sobre el plan de **7.427 buses** (corrida de octubre), no sobre el de cuartetos. Hay que agregar el plan de cuartetos para recalcularlos. La diferencia entre ambos planes es de 1,0 % en buses y 0,8 % en costo, así que las conclusiones cualitativas se mantienen. Los hallazgos (día laboral):

- **Ahorro contra el caso base (plan de 7.427):** −14,5 % de buses y −13,9 % de costo; los km en vacío bajan 31,0 %.
- **Los cargadores no son el cuello de botella.** El pico es de 21 a 45 buses cargando a la vez, entre 17,5 % y 26 % de las conexiones, entre las 17:00 y las 19:30, antes del tramo caro (19:00 a 22:00). El caso base llena las conexiones de E2, E4 y E5 entre las 20:00 y las 22:00.
- **El espacio sí se llena.** Exactamente 700 buses terminan el día estacionados en un electroterminal (la capacidad total: 180 + 150 + 150 + 120 + 100); en el caso base, ninguno.
- **Desbalance entre sectores.** El sector 3 (Los Espinos) carga solo 34 % de su energía en su propio electroterminal; los demás cargan entre 53 % y 77 % en el suyo.
- **La energía casi no pesa:** 0,4 % del costo. Se carga el 3,0 % de la energía consumida, porque los buses parten llenos y terminan con 71 kWh en promedio.

## 8. Límites que hay que decir en voz alta

1. **El día siguiente no se repite solo.** Para volver a partir con batería llena habría que reponer 2,07 GWh de noche. Con las 700 conexiones a 180 kW tomaría 16,4 h el día laboral (10,8 h el sábado, 9,3 h el domingo), y 6.727 de los 7.427 buses terminan en terminales sin cargadores. El equipo docente ya lo preguntó el 8-oct.
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
