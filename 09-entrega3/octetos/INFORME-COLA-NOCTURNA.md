# Informe de la cola nocturna · 22-nov-2026

Grupo 29 · ICS2122 · Entrega 3
Resultados de las corridas del 22-nov (01:37 a 17:35). Todas las cifras salen de los CSV de `09-entrega3/octetos/resultados/`. El informe general de la entrega está en [`09-entrega3/INFORME-RESULTADOS.md`](../INFORME-RESULTADOS.md); este documento entra en el detalle de lo nuevo.

## 1. En una página

- **Sin recarga forzada (batería de 350 kWh), la exacta resuelve casos de hasta 293 corridas en menos de 5 minutos.** Con eso tenemos el óptimo demostrado en rutas_06, rutas_08, rutas_10 y mediano_200. En los dos casos donde corrimos heurísticas, los cuartetos quedan a **+0,57 %** (rutas_10) y **+0,03 %** (mediano_200) del óptimo.
- **Con recarga forzada (150 y 120 kWh), la exacta ya no demuestra el óptimo en 15 minutos.** Su mejor plan queda entre 1,8 % y 15,5 % sobre su cota.
- **Con recarga, la mejor heurística queda en promedio 4,8 % sobre la exacta con 150 kWh y 2,8 % con 120 kWh** (peor caso: +6,8 %). Sin recarga la diferencia era de 0,13 %. Casi toda la diferencia está en los buses: la heurística usa de 0 a 4 buses más.
- **Darle más tiempo a la heurística no ayuda.** Pasar de 2 a 15 minutos baja el costo de los cuartetos en 0,2 % en promedio (como máximo 1,8 %), y en 6 de 10 casos la búsqueda se detiene sola antes de los 15 minutos. La diferencia con la exacta no es falta de tiempo: es el límite del vecindario.
- **En el caso más grande con recarga (rutas_10 con 150 kWh, 293 corridas), la heurística le gana a la exacta:** 62 buses y USD 19.625 contra 64 buses y USD 19.697 tras 1 hora.
- **No se alcanzó a correr:** la exacta de rutas_12, las heurísticas de rutas 6, 8 y 12, y los medianos de 250 a 400 corridas (sección 7).

## 2. Qué se corrió

Hubo dos colas: la nocturna (01:37 a 13:30) y una segunda en la tarde (14:43 a 17:35) para probar si 15 minutos de heurística cerraban la diferencia.

| Etapa | Casos | Tiempo por caso | Estado |
|---|---|---|---|
| Exacta, batería 150 kWh | 5 chicos | 15 min | Terminada; ninguno demuestra el óptimo |
| Exacta, batería 350 kWh | rutas_10, mediano_200 | hasta 1 h / 40 min | Óptimo en ambos |
| Heurísticas, 150 kWh | 5 chicos | 2 min | Terminada |
| Heurísticas, 350 kWh | rutas_10, mediano_200 | 5 min | Terminada |
| Exacta y heurísticas, 120 kWh | 5 chicos | 15 min / 2 min | Terminada |
| Exacta, 350 kWh | rutas_06, 08, 12 | 1 h | 06 y 08 óptimos; 12 cortado a los ~34 min |
| Heurísticas rutas 6, 8, 12 · medianos 250–400 | — | — | **No corrieron** (cola cortada a las 13:23) |
| Cuartetos y pares-tríos, 150 y 120 kWh | 5 chicos | 15 min | Terminada (cola de la tarde) |
| Exacta y heurísticas, 150 kWh | rutas_10 | 1 h / 15 min | Terminada (cola de la tarde) |

Las heurísticas son: **pares-tríos** (mitad del tiempo intercambiando corridas entre 2 buses y mitad entre 3) y **cuartetos al azar** (semilla 1). El **plan inicial** es el que arma nuestro método antes de mejorarlo; **no** es el caso base miope del informe general.

## 3. Sin recarga forzada: casos de 6 a 10 rutas

| Caso | Corridas | Óptimo (exacta podada) | Tiempo de la exacta | Cuartetos 5 min | Diferencia |
|---|---|---|---|---|---|
| rutas_06 | 129 | 24 buses · USD 7.506,30 | 51 s | sin correr | — |
| rutas_08 | 200 | 38 buses · USD 11.517,04 | 185 s | sin correr | — |
| mediano_200 | 200 | 24 buses · USD 8.177,94 | 79 s | 24 buses · USD 8.180,38 | +0,03 % |
| rutas_10 | 293 | 60 buses · USD 18.204,24 | 258 s | 60 buses · USD 18.307,52 | +0,57 % |

En rutas_10, el plan inicial tiene 61 buses (USD 18.565,79) y pares-tríos con 5 minutos no baja buses (61, USD 18.472,52). Los cuartetos sí sacan el bus que sobra.

**Lectura:** sin recarga, la exacta podada escala bien (293 corridas en 4 minutos) y la heurística queda a menos de 1 % del óptimo, igual que en los casos chicos.

## 4. Con recarga forzada: batería de 150 kWh

Se copiaron los 5 casos chicos con una batería de 150 kWh para que los buses *tengan que* recargar durante el día.

| Caso | Corridas | Plan inicial | Mejor heurística | Exacta (15 min) | Cota de la exacta | Heurística vs exacta |
|---|---|---|---|---|---|---|
| chico_02 | 84 | 33 · 9.957 | 31 · 9.360 | 29 · 8.933 | 8.776 (1,8 %) | +4,8 % |
| chico_03 | 116 | 40 · 12.242 | 28 · 8.923 | 26 · 8.422 | 8.147 (3,3 %) | +5,9 % |
| chico_04 | 152 | 65 · 20.285 | 46 · 15.114 | 42 · 14.157 | 13.633 (3,7 %) | +6,8 % |
| chico_05 | 157 | 64 · 20.458 | 49 · 16.803 | 49 · 16.646 | 14.062 (15,5 %) | +0,9 % |
| chico_06 | 141 | 42 · 12.465 | 31 · 9.544 | 29 · 9.055 | 8.435 (6,8 %) | +5,4 % |
| **rutas_10** | **293** | 77 · 23.283 | **62 · 19.625** | 64 · 19.697 (1 h) | 18.213 (7,5 %) | **−0,4 %** |

Formato: buses · USD por día. Entre paréntesis, cuánto queda el plan de la exacta sobre su cota. La «mejor heurística» es el plan más barato entre pares-tríos y cuartetos, con 2 o 15 minutos.

- La heurística mejora el plan inicial entre **6 % y 27 %**.
- Contra la exacta queda **+4,8 % en promedio** en los chicos. Casi todo son buses: la heurística usa 2 buses más en tres casos, 4 más en chico_04 y los mismos en chico_05.
- En rutas_10 pasa lo contrario: la exacta no alcanza a ordenar 293 corridas en 1 hora (con 2 hilos), y los cuartetos le ganan por 2 buses.

## 5. Con recarga forzada: batería de 120 kWh

| Caso | Corridas | Plan inicial | Mejor heurística | Exacta (15 min) | Cota de la exacta | Heurística vs exacta |
|---|---|---|---|---|---|---|
| chico_02 | 84 | 39 · 11.910 | 32 · 10.198 | 31 · 9.964 | 9.775 (1,9 %) | +2,3 % |
| chico_03 | 116 | 47 · 14.228 | 36 · 11.498 | 34 · 11.022 | 10.248 (7,0 %) | +4,3 % |
| chico_04 | 152 | 79 · 24.145 | 58 · 19.158 | 58 · 19.157 | 17.006 (11,2 %) | +0,0 % |
| chico_05 | 157 | 73 · 22.967 | 57 · 19.238 | 57 · 19.124 | 17.539 (8,3 %) | +0,6 % |
| chico_06 | 141 | 46 · 14.165 | 34 · 10.714 | 32 · 10.047 | 8.566 (14,7 %) | +6,6 % |

- La heurística mejora el plan inicial entre **14 % y 24 %**.
- Contra la exacta queda **+2,8 % en promedio**; en chico_04 y chico_05 empata en buses.
- Con menos batería hacen falta más buses: chico_04 pasa de 42 (150 kWh) a 58 (120 kWh) en la exacta.

**Ojo con la palabra «brecha».** La exacta no demuestra el óptimo con recarga, así que «heurística vs exacta» es la distancia al **mejor plan conocido**, no al óptimo. El óptimo está entre la cota y el plan de la exacta. En el peor caso posible, la heurística queda 25 % sobre el óptimo (chico_06 con 120 kWh, contra la cota). No sabemos dónde está realmente el óptimo dentro de ese rango.

## 6. ¿Ayuda darle 15 minutos a la heurística?

La cola de la tarde repitió las heurísticas de los 10 casos chicos con 15 minutos en vez de 2.

**Cuartetos:** casi no cambian.

| Batería | Cambio de costo de 2 a 15 min | Casos que paran solos antes de 15 min |
|---|---|---|
| 150 kWh | −0,01 % a −0,36 % | 4 de 5 |
| 120 kWh | 0,00 % a −1,76 % | 2 de 5 |

El único bus que se gana es en chico_05 con 120 kWh (59 → 58). Cuando la búsqueda para sola es porque probó todo su vecindario y no encontró nada mejor; más tiempo no la mueve.

**Pares-tríos:** en 5 de 10 casos el plan con 15 minutos es **peor** que con 2 (entre +1,7 % y +2,4 %, uno o dos buses más). Lo más probable es que se deba a cómo reparte el tiempo: con 2 minutos, los pares se cortan a los 60 s y los tríos parten de un plan todavía flexible. Con 15 minutos, los pares llegan hasta el fondo de su óptimo local y los tríos no logran salir de ahí. No lo hemos verificado.

**Conclusión:** la distancia de 0 a 7 % con la exacta no se cierra con más tiempo. Para cerrarla habría que cambiar el vecindario (por ejemplo, grupos que muevan recargas entre buses), no correr más rato.

## 7. Lo que falta y un problema en los logs

**No corrió:**
- La exacta de rutas_12 (442 corridas): se cortó a los ~34 minutos sin resultado.
- Las heurísticas de rutas_06, rutas_08 y rutas_12.
- Los medianos de 250 a 400 corridas (exacta y heurísticas).

A las 13:23 se cortó la cola porque el Mac estaba muy caliente con 4 hilos. Las etapas que quedaban fallaron al arrancar Python (`TimeoutError` al cargar el entorno virtual) y no dejaron filas en los CSV.

**El log miente con el código de salida.** `noche.log` y `recarga_15min.log` dicen «código 0» en todas las etapas, incluso en las que fallaron, porque el script guarda la fecha antes de leer el código. Para saber si una etapa terminó bien hay que mirar si dejó filas en el CSV, no el log.

## 8. Qué decir en la presentación

1. **Sin recarga, el método está a menos de 1 % del óptimo** (0,13 % en los chicos, 0,57 % en 293 corridas).
2. **Con recarga forzada, queda a 0–7 % del mejor plan conocido**, y en el caso más grande es **mejor** que la exacta con 1 hora.
3. **La diferencia no es de tiempo de cómputo**: con 15 minutos queda igual. Es una limitación del vecindario cuando las recargas importan, y es la mejora natural para un trabajo futuro.
4. En la red completa (batería de 350 kWh) los buses casi no recargan, así que el escenario relevante para nuestro resultado principal es el de la sección 3.

## 9. Archivos

| Qué | Archivo (en `09-entrega3/octetos/resultados/`) |
|---|---|
| Heurísticas con 150 kWh (2 y 15 min) | `recarga_bat150.csv` |
| Exacta con 150 kWh | `recarga_bat150_exacta.csv` |
| Heurísticas con 120 kWh (2 y 15 min) | `recarga_bat120.csv` |
| Exacta con 120 kWh | `recarga_bat120_exacta.csv` |
| Casos de 6 a 10 rutas (350 kWh) | `casos_rutas.csv`, `casos_rutas_exacta.csv` |
| mediano_200 exacta | `casos_medianos_exacta_podada.csv` |
| Logs | `noche.log` (cola nocturna), `recarga_15min.log` (cola de la tarde) |

Cada fila trae `presupuesto_s` (120 = 2 min, 900 = 15 min), `motivo_fin` («presupuesto» = se acabó el tiempo; «sin_mejoras_en_vecindario» = paró sola), y para la exacta, `optimo` (True/False) y `cota_usd`.
