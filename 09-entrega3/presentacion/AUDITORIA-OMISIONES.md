# Auditoría de omisiones del deck (23-nov-2026)

**Qué se cruzó.** Las 20 láminas de `deck.html` (texto en pantalla y notas) contra:
- los lineamientos de la Entrega 3 (rúbrica de 60 pts y contenido pedido);
- el feedback del 8-oct (marcas [F] en `08-entrega2/informe2/ESQUEMA.md`);
- `AUDITORIA-RUBRICA.md` y `ASIGNACION-LAMINAS-12-20.md`;
- `INFORME-RESULTADOS.md` y `octetos/INFORME-COLA-NOCTURNA.md`;
- los CSV de `octetos/resultados/`, incluidos los que todavía no tienen commit.

**Qué no se cruzó.** El informe escrito. Tampoco la versión de Canva de las láminas 12–14, que difiere del HTML.

## Estado después de las correcciones (23-nov, en `deck.html`)

El deck pasó a **21 láminas y 5 anexos**. Lo resuelto:

| Hallazgo | Cómo se resolvió |
|---|---|
| Cola nocturna ausente (#1, #3) | Lámina nueva 18 con dos paneles: casos medianos sin recarga (0,03 a 4,93 %) y recarga forzada (+4,8 % y +2,8 % contra la exacta). Se destacan los 62 contra 64 buses y el «−0,2 % con más tiempo». |
| Sesgo de casos chicos (#2) | Los casos medianos están en la lámina 18; la 17 define qué es el óptimo, dónde se mide y qué es la brecha. |
| Construcción contra mejora (#5) | En la lámina 15 y sus notas: el 84 % de la baja ya la logra el plan inicial. |
| KPI de la lámina 6 (#6) | La lámina 16 muestra el km en vacío como % (11,9 contra 16,3 %), los buses cargando a la vez (38 contra 180) y la energía cargada (−87 %). La 20 da el caso base al cierre (140 kWh). |
| «Corrida» sin definir | Definida en la lámina 3. |
| Eje de la lámina 5 | Título «Corridas en curso a la vez». |
| Alcance de la auditoría | La lámina 11 dice qué no certifican los auditores. |
| 7.351 repetido | En la lámina 17 dice «Nuestro plan», sin la cifra. |
| Tiempo | Notas de las láminas 12–21 recortadas a 2,3 palabras por segundo: el deck declara 14:00. |

**Espacio reservado** (recuadro punteado con «PENDIENTE»; en el .pptx es una forma que se puede borrar):
- **Lámina 18:** rutas_12 (442 corridas) y casos de 250 a 400 corridas.
- **Lámina 19:** incertidumbre (atrasos y tiempos de viaje) y escenarios de consumo, batería, costos y espera.
- **Anexos A1 a A5:** MILP de recarga, familias descartadas, supuestos, tabla caso por caso y sectores fijos.

**Sigue abierto:**
- **Lámina 5:** las notas habladas duran unos 70 s y declaran 50.
- **Feedback «en qué horarios cargan»:** se menciona en las notas de la 16, pero sin figura.
- **Expositores (D7) y ensayos.**
- **Canva:** está desactualizado y hay que reemplazarlo completo, porque ahora todas las láminas dicen «/ 21».

## Lo más grave

| # | Qué falta | Por qué importa | Severidad |
|---|---|---|---|
| 1 | **Toda la cola nocturna: recarga forzada (150 y 120 kWh)** | Los lineamientos piden «qué pasa si los supuestos no se cumplen». El profesor pidió ver casos donde los buses *tienen que* recargar. No aparece en ninguna lámina ni en las notas. | Alta |
| 2 | **Los casos medianos (129 a 293 corridas), que no siempre dan menos de 1 %** | La lámina 17 solo muestra los 5 casos chicos (0,13 %). Con óptimo demostrado: mediano_200 +0,03 %, rutas_10 +0,57 %, rutas_06 +0,96 % y **rutas_08 +4,93 % (40 buses contra 38)**. Estos dos últimos son de la cola del 23-nov (commit 48fc397). Mostrar solo los chicos es un sesgo de selección que un profesor puede detectar. | Alta |
| 3 | **«Más tiempo no ayuda»: el límite es el vecindario** | Con recarga, pasar de 2 a 15 min baja el costo apenas 0,2 %. La diferencia con la exacta (0 a 7 %) no se cierra con tiempo. Es el análisis crítico y la extensión natural que piden los lineamientos (vecindarios que muevan recargas). | Alta |
| 4 | **Incertidumbre (atrasos y tiempos de viaje variables)** | Los lineamientos la nombran explícitamente («comportamiento frente a incertidumbre»). La tarea T9 del plan nunca se hizo. Hoy solo aparece como «falta» en la lámina 20. Hay que decirlo como limitación explícita, con su porqué. | Alta |
| 5 | **De dónde sale el ahorro: construcción contra mejora** | Caso base 8.684 → plan inicial 7.570 → cuartetos 7.351. El 84 % de los buses ahorrados (1.114 de 1.333) y el 86 % del costo ahorrado vienen de la **construcción**, que comparte buses entre rutas del mismo sector. Los cuartetos aportan el resto (−219 buses, −2,25 %). La lámina 16 atribuye el ahorro a «buses» pero no a qué parte del método. | Alta |
| 6 | **Los KPI de la lámina 6 no se cierran todos contra el caso base** | Ver la tabla de KPI. La lámina 6 promete «seis indicadores, siempre contra el caso base», y dos no aparecen comparados. | Media |

## KPI prometidos (lámina 6) contra lo que se muestra

| KPI (como se define en la lámina 6) | Caso base → plan (día laboral) | Dónde aparece | Problema |
|---|---|---|---|
| Buses | 8.684 → 7.351 | 15 | — |
| Costo total, USD/día | 3.062.717 → 2.617.469 | 15 | — |
| Km en vacío, **% de los km** | 16,3 % → 11,9 % | 16 («−30 %») | Se muestra la caída de km, no el % que define la lámina 6. Mostrar 16,3 % → 11,9 % o cambiar la definición. |
| Buses cargando a la vez, **máximo por electroterminal** | hasta 180 → 15 a 38 | 16 («21 %» de las conexiones) | Se muestra en % de conexiones, no en buses. Sin el valor del caso base. |
| Energía cargada en el día, kWh | 427.122 → 53.922 (−87 %) | **No aparece** | Falta. |
| Energía al cerrar el día, kWh por bus | 140 → 66 | 19 (solo 66) | Falta el caso base: el plan termina con **menos** energía que el caso base, y eso es parte del hallazgo de la lámina 19. |

## Feedback del 8-oct sin cerrar

| Comentario [F] | Estado |
|---|---|
| Definir corridas, cadenas, traslados en vacío y jornadas | **Abierto.** «Corrida» no se define en la lámina 3. «Traslado en vacío» y «jornada» aparecen en las láminas 13 y 14 sin definir. El deck mezcla «viaje» (láminas 5 y 10) con «corrida». |
| Peso de cada costo, en el caso base y en el plan | **Parcial.** La lámina 4 da el 70,2 % del plan; la 16 da diferencias, no composición. Caso base: buses 70,9 %, km 26,2 %, energía 2,6 %, sesiones 0,2 %. Plan: 70,2 / 29,2 / 0,4 / 0,2 %. |
| En qué horarios cargan los buses (energía por hora con la tarifa encima) | **Abierto.** Dato disponible: el pico del plan es entre 19:25 y 19:55, justo al inicio del tramo caro (19:00 a 22:00); el caso base llena las conexiones entre las 20:00 y las 22:00. Hay figuras listas en `kpi/resultados/uso_e_perfil_L.png`. |
| Si el caso base carga, ¿la diferencia sería igual? | Cerrado solo en las notas de la lámina 16. |
| Toda comparación con valor, Δ y Δ % contra el caso base | Parcial (ver la tabla de KPI). |
| Justificar la comparación contra la cota | Cerrado en la lámina 17. |

## Resultados del repo que no están en el deck

| Resultado | Fuente | Sugerencia |
|---|---|---|
| Recarga forzada: la heurística mejora el plan inicial entre 6 % y 27 % (150 kWh) y entre 14 % y 24 % (120 kWh) | `recarga_bat150*.csv`, `recarga_bat120*.csv` | Lámina o paso nuevo (#1) |
| Con recarga, la exacta no cierra en 15 min: la heurística queda +4,8 % (150 kWh) y +2,8 % (120 kWh) sobre el **mejor plan conocido**, no sobre el óptimo | Ídem | Decirlo con la palabra correcta: «contra el mejor plan de la exacta» |
| En rutas_10 con 150 kWh (293 corridas), los cuartetos **le ganan** a la exacta tras 1 h: 62 contra 64 buses | `recarga_bat150*.csv` | Es el dato más llamativo de la cola. |
| Casos medianos con óptimo demostrado (#2) | `casos_rutas*.csv`, `casos_medianos_exacta_podada.csv` | Agregar a la lámina 17 |
| Pares y tríos le gana a cuartetos en rutas_06 y rutas_08 (5 min, una semilla) | `casos_rutas.csv` | Matiza «el mejor tamaño es 4». Decirlo en las notas. |
| Elegir al azar le gana a elegir buses parecidos (cuartetos parecidos se estanca en 7.496) | `red_completa_417_L.csv` | Es la parte creativa; cabe en las notas de la 17. |
| 700 buses terminan en los electroterminales y 6.651 en terminales sin cargador | `kpi/resultados/plazas_metodo_L_resumen.csv` | Refuerza la lámina 19. |
| Desbalance de sectores: Los Espinos carga solo el 37,6 % en su propio electroterminal | `kpi_planes.md` | Anexo o notas de la 16. |
| Sábado: el uso de conexiones llega a 41 % (La Reina) | `uso_e_resumen.csv` | La lámina 16 dice «21 % como máximo»: aclarar que es el día laboral. |
| Energía: 0,4 % del costo; se carga el 2,5 % de lo que se consume | `kpi_planes.md` | Explica por qué el ahorro no es energía (lámina 16). |

## Limitaciones que nadie dice en voz alta

| Limitación | Dónde debería ir |
|---|---|
| El costo de espera (0,03 USD/min) no se cobra en ningún plan (decisión D2 sin cerrar) | Lámina 20 o notas de la 15; anexo |
| El límite del transformador no viene en los datos: se modeló como conexiones × 180 kW | Lámina 20 o anexo |
| Los resultados de casos medianos y de recarga son de **una** semilla | Notas de la 17 |
| Los auditores no certifican turnos, transformador, reposición nocturna, terminales finitos, espera ni óptimo global (`AUDITORIAS_Y_CAMBIOS.md`) | Lámina 11, una línea; hoy dice «todos los planes fueron auditados» sin matiz |
| Consumo, batería y potencia fijos en el código (no sensibilizados) | Solo en las notas de la 18; pasarlo a la lámina 20 |

## Pendientes de la auditoría anterior (láminas 1–11)

- Lámina 3: definir «corrida».
- Lámina 5: el eje vertical de la curva no tiene título ni unidad.
- Lámina 7: el peso de cada costo del caso base (se puede cerrar en la 16).
- Lámina 11: la lista de lo que los auditores no certifican.
- Anexos: el deck no tiene ninguno. Banco de preguntas sin lámina de respaldo: ¿por qué no respetan los 1.200 buses?, ¿por qué sectores fijos?, atrasos, 18 km/h en vacío, transformador, espera, MILP de recarga, descarte de las seis familias.

## Forma y consistencia

- **Cifras repetidas.** 7.351 aparece en las láminas 15 y 17; las reglas solo permiten repetir 8.684 y 6.601. «100 %» aparece en las láminas 7, 14 y 19.
- **Cota.** `INFORME-RESULTADOS.md` usa una cota de **costo** (USD 2.322.956, brecha 12,7 %). La lámina 17 usa una cota de **buses** (6.601, +11,4 %). Las dos son correctas, pero el informe y el deck deben decir lo mismo.
- **Canva y HTML.** Las láminas 12–14 del HTML son la versión mejorada; Canva tiene la del compañero, corregida. Las 15–20 no están en Canva.
- **Tiempo.** Las notas suman unas 13:45 (láminas 1–11: 7:20; 12–14: 1:40; 15–20: 4:45). Agregar la recarga forzada (~40 s) deja el deck en ~14:25, dentro de la meta de 14:00 a 14:30. Si se agrega algo más, hay que cortar en otra parte.
- **Equipo de exposición (D7).** Sigue abierto; tampoco hay ensayos con cronómetro.

## Pendiente de datos

- La cola de rutas 6, 8 y 12 terminó el 23-nov a las 00:35 y tiene commit (48fc397). En rutas_12 (442 corridas) cuartetos da 84 buses, igual que el plan inicial; el caso no tiene óptimo porque la exacta se cortó.
- Siguen sin correr los casos de 250 a 400 corridas.
