# Contexto del proyecto: lo que está hecho y lo que falta

Grupo 29 · ICS2122 Taller de Investigación Operativa (Capstone) · 2026-2
Problema P7: planificación de la operación de buses eléctricos en la Región Metropolitana.
Escrito el **22-nov-2026** para que cualquier integrante, o la IA con la que trabaje, pueda seguir
sin haber estado en las sesiones anteriores. Las cifras se comprobaron ese día contra los archivos
del repositorio.

Repositorio (público): https://github.com/nfariasl/capstone-buses-electricos

---

## 0. Cómo usar este documento

- **Si eres del grupo:** lee las secciones 1, 2 y 9 (estado y lo que falta). El resto es de consulta.
- **Si eres una IA:** lee el documento completo antes de tocar nada. Después, lee el documento
  específico de la tarea que te pidan (sección 13). Respeta las reglas de la sección 10: casi todas
  vienen de errores que ya pasaron.
- **Prompt sugerido para empezar con otra IA** (Claude, ChatGPT, Gemini, Cursor, etc.):

  > Estoy en el proyecto Capstone del Grupo 29 (buses eléctricos de RED). Lee primero
  > `CONTEXTO-DEL-PROYECTO.md` en la raíz del repo, luego `README.md` y el documento que corresponda a
  > mi tarea según la sección 13. Mi tarea es: «…». No inventes cifras: cada número debe salir de un
  > archivo del repo, y dime de cuál. Antes de cambiar código de `metodo_hibrido/`, lee la sección 10.

---

## 1. El proyecto en un minuto

**Qué decidimos.** Cuántos buses eléctricos hacen falta y qué hace cada uno durante el día: qué
corridas cubre, cuándo y dónde recarga y dónde termina estacionado.

**Qué minimizamos.** El costo diario: USD 250 por bus + USD 0,5 por km recorrido + energía (USD 0,10 a
0,22 por kWh, según la hora) + USD 5 por sesión de carga. Los buses son cerca del 70 % del costo, así
que el método ataca primero el tamaño de la flota.

**Sujeto a:**
- cubrir **todas** las corridas (64.502 en día laboral, 417 rutas);
- batería de 350 kWh, reserva mínima de 35 kWh (10 %) y consumo de 1,4 kWh/km;
- carga de hasta 180 kW, en bloques de 5 min, con carga parcial permitida;
- 5 electroterminales (E1 Vespucio Norte, E2 El Conquistador, E3 Los Espinos, E4 La Reina,
  E5 Santa Rosa), con 700 plazas en total; cada plaza tiene su conexión;
- velocidad de 18 km/h en los traslados en vacío.

En la literatura el problema se llama **MD-E-VSP** (*Multi-Depot Electric Vehicle Scheduling
Problem*) con programación de recargas.

**Integrantes** (según la portada del deck final): Nicolás Farías, Gustavo Cueto, Fernando Gonzalez,
Diego Barrios, Gustavo Anguita, Cristobal Rehbein y Ricardo Palma. Ayudante: Max Burr.

---

## 2. Estado al 22-nov-2026

| Frente | Estado | Detalle |
|---|---|---|
| Entrega 1 (datos, problema, KPIs) | ✅ Entregada | §3.1 |
| Interrogación 1 (29-sep) | ✅ Rendida | §3.1 |
| Entrega 2 (presentación 8-oct, informe 16-oct) | ✅ Entregada | §3.2 |
| Método final: cuartetos al azar en la red completa, L / S / D | ✅ Corrido y comparado | §5.1 |
| Distancia al óptimo en casos chicos (exacta) | ✅ 0,13 % en promedio | §5.3 |
| Casos con recarga forzada (150 y 120 kWh) | ✅ Corridos | §5.4 |
| KPI y uso de electroterminales | ✅ Recalculados el 22-nov sobre el plan de cuartetos (semilla 1) | §5.5 |
| Sensibilidad | 🟡 Escenarios definidos, **sin resultados** en el repo | §9 C |
| Repetibilidad del día siguiente | ✅ Calculada por electroterminal (22-nov): en día laboral se cubre el 45 % | §9 D |
| Incertidumbre (atrasos, Monte Carlo) | 🔴 Sin empezar | §9 E |
| Deck final (15 min) | 🟡 Láminas 1–11 hechas; **faltan las 12–20** | §9 A |
| Informe final (45 págs., 200 pts) | 🔴 **Sin empezar** en el repo | §9 F |
| Repositorio final | 🟡 Público y ordenado; falta la etiqueta `entrega-3` | §9 H |

**Fechas.** Los lineamientos no las traen. Lo último que se manejó: presentación **alrededor del
24-nov** e informe el **viernes 27-nov** (fin de clases UC). **Hay que confirmarlas en Canvas.**

---

## 3. Cronología: qué se hizo en cada entrega

### 3.1 Entrega 1 (septiembre)

- **Análisis de datos** del GTFS de RED (`02-analisis-datos/analisis_datos.py` → `03-resultados/`).
  Solo buses (`route_type == 3`), día laboral.
- **Cifras finales del informe 1:** **417 rutas, 64.502 corridas laborales y una cota de 6.601 buses
  en circulación a la vez a las 08:00**. Mandan sobre las del deck de la Entrega 1 (418 / 64.603 /
  6.603), que salieron de un procesamiento anterior; esas no se usan.
- Documentos de trabajo en `04-documentos/`: análisis de datos, supuestos, discusión metodológica,
  bibliografía (23 referencias verificadas) y preguntas al profesor.
- Metodología propuesta entonces: red tiempo-espacio con descomposición de flujo en 3 fases (Olsen et
  al., 2020), sectorizada por electroterminal.
- Entregables en `05-entrega1/` (informe en PDF y presentación).
- La Interrogación 1 fue el 29-sep; su guía de estudio se sacó del repo el 11-nov.

### 3.2 Entrega 2 (octubre)

**Evolución del método** (sirve para el capítulo de evolución metodológica del informe final):

1. **Fase 1** (`codigo/fase1/`): flujo de costo mínimo en una red tiempo-espacio **sin batería**. Da
   una cota y cadenas de corridas.
2. **Prototipo de tres fases** (`codigo/tres_fases/`): flujo → cadenas → jornadas con recarga. En la
   muestra de 212 rutas: 4.175 buses y USD 1.459.573.
3. **Método híbrido** (`metodo_hibrido/`), el que quedó:
   - *Construcción cronológica*: recorre las corridas por hora de salida y asigna cada una al bus del
     mismo sector que puede tomarla (horario y energía) con menos km en vacío. Solo abre un bus nuevo
     si no hay candidato. Es Python puro, sin Gurobi.
   - *Mejora local*: toma grupos de jornadas (pares, tríos), propone repartos de corridas entre ellas y
     un **MILP local** (`conjunta.py`, con Gurobi) decide las recargas y terminales de esas jornadas,
     con las demás fijas. Solo acepta mejoras estrictas que pasan la auditoría.
   - *Auditoría* (`verificar.py`): cobertura, horarios, continuidad, energía, plazas, conexiones y
     costos. Hay además un auditor independiente que reconstruye todo desde el GTFS.

**Caso base oficial:** la **política miope por ruta con recarga** (`codigo/tres_fases/caso_base.py`,
umbral 0 %, el más favorable de los probados). Cada ruta usa sus propios buses y recarga al 100 %
cuando no le alcanza. Está documentada en `codigo/tres_fases/CASO_BASE.md`. La pidieron el profesor y el
ayudante («que incluya carga aunque sea de manera básica»). Reemplazó al caso base sin recargas
(5.150 buses, `caso_base_simple_gurobi/`) que se mostró el 8-oct.

**Resultados del informe 2** (muestra de 212 rutas, 33.220 corridas):
- caso base miope: 4.509 buses y USD 1.601.775;
- híbrido refinado: **3.873 buses y USD 1.374.632** (−14,1 % de buses y −14,2 % de costo; −12,4 % si se
  ajusta por la energía con que termina cada plan);
- la red completa de 417 rutas quedó **fuera** del informe 2.

**Otros productos:**
- barrido del presupuesto de búsqueda (15 corridas, `08-entrega2/sensibilidad_presupuesto/`);
- informe en LaTeX con cifras generadas por script (`08-entrega2/informe2/`, `./compilar.sh`);
- la presentación que expuso el grupo, en `08-entrega2/presentacion2_grupo.pdf`.

**Feedback del ciclo 2 que sigue vigente** (descuenta si no se atiende en la Entrega 3):
- número de lámina en todas;
- supuestos explícitos sobre lo que no está en los datos (tráfico, mantenciones);
- ningún porcentaje sin decir de dónde sale;
- decir de dónde salen los costos antes de mostrarlos;
- comparar los KPIs contra el caso base, no contra metas fijas;
- justificar la comparación contra la cota inferior aunque no sea factible;
- definir corrida, cadena, traslado en vacío y jornada;
- mostrar el peso de cada costo y en qué horario cargan los buses;
- **«¿Cómo se cubre el día siguiente?»** (repetibilidad energética).

### 3.3 Entrega 3 (27-oct a hoy)

El plan completo está en `09-entrega3/PLAN-ENTREGA3.md`. Lo que se hizo:

1. **27-oct · Red completa en los tres tipos de día.** Se prepararon sábado y domingo
   (`preparar_completa.py --servicio`) y se corrieron con el híbrido de la Entrega 2; el caso base
   miope se corrió en L, S y D. Todo está auditado (`metodo_hibrido/resultados/completa_417_*` y
   `codigo/output/tres_fases/red_417_*_caso_base/`).
2. **9 al 11-nov · Estudio de tamaños de grupo** (`09-entrega3/octetos/`; plan en
   `PLAN-PARES-TRIOS-OCTETOS.md`).
   - La mejora se generalizó a grupos de k = 3 a 8 buses (`metodo_hibrido/grupos.py`), elegidos
     «parecidos» (horarios similares) o «al azar» (con semilla).
   - Se agregó una mezcla creciente tipo VNS (`creciente.py`) y el modelo **exacto** (`exacto.py`)
     para casos chicos.
   - **Decisión del grupo: gana el método más barato con el mismo tiempo.** Ganó **cuartetos al
     azar** (`elegir_metodo.py`, `UMBRAL = 0.0`).
3. **11-nov · Mapa de sectores**, un informe de 2 páginas en lenguaje simple y la metodología en 2
   páginas (`09-entrega3/mapa_sectores/`).
4. **17 al 22-nov · KPI** de todos los planes y uso de los electroterminales hora a hora
   (`09-entrega3/kpi/`), a pedido del profesor en la reunión del 17-nov.
5. **22-nov · Escenarios de sensibilidad definidos** (`09-entrega3/sensibilidad/`), sin correr.
6. **22-nov · Cola nocturna**: casos con recarga forzada (baterías de 150 y 120 kWh) y la exacta
   «podada» en casos de 6 a 10 rutas, a pedido del profesor y de Gustavo
   (`09-entrega3/octetos/INFORME-COLA-NOCTURNA.md`).
7. **22-nov · Deck final** en HTML (láminas 1–11), exportado a PPTX para Canva
   (`09-entrega3/presentacion/`), con una auditoría contra la rúbrica y la guía de las láminas 12–20.
8. **22-nov · Informe de resultados para el grupo** (`09-entrega3/INFORME-RESULTADOS.md`).
9. **22-nov · Repositorio público**, para que todo el grupo pueda clonarlo.

---

## 4. El modelo y los supuestos (lo que hay que poder defender)

| Supuesto | Valor | Por qué / ojo |
|---|---|---|
| Tipos de día | L, S y D por separado; semana = 5 L + S + D | La flota necesaria es la del día laboral |
| Batería inicial | 100 % al inicio del día | El día **no se repite solo** (§5.6) |
| Batería, reserva y consumo | 350 kWh, 35 kWh y 1,4 kWh/km | Fijos en el código; para cambiarlos, ver §10 |
| Carga | Hasta 180 kW, bloques de 5 min, parcial | `transformer_mw` está en el diccionario de datos pero **no viene en ningún archivo**; el límite se modeló como conexiones × 180 kW |
| Electroterminales | 5, con 700 plazas, cada una con su conexión | Recursos compartidos entre sectores |
| Terminales comunes | T01–T04: estacionamiento ilimitado, sin carga; Los Acacios excluido | |
| Sectores | Cada ruta va al electroterminal con menos km en vacío; cada bus atiende un solo sector | 65 / 95 / 68 / 72 / 117 rutas |
| Velocidad en vacío | 18 km/h constante | Pregunta probable |
| Costo de espera (0,03 USD/min) | **No se cobra** | Sumaría unos USD 21–22 mil/día a ambos planes (medido en la muestra de 212 rutas); no cambia la comparación |
| Tiempos de viaje | Los del GTFS, sin tráfico ni mantenciones | Limitación que hay que declarar |

---

## 5. Resultados (cifras verificadas el 22-nov)

### 5.1 Resultado principal: red completa, cuartetos al azar, 40 min (2.400 s)

Promedio de 3 semillas. Fuente: `09-entrega3/octetos/resultados/red_completa_417_{L,S,D}.csv`. El caso
base sale de `09-entrega3/kpi/resultados/kpi_planes.md`.

| Día | Corridas | Caso base miope | **Cuartetos al azar** | Diferencia |
|---|---|---|---|---|
| Laboral | 64.502 | 8.684 buses · USD 3.062.717 | **7.351 buses · USD 2.617.469** | −15,4 % buses · −14,5 % costo |
| Sábado | 43.619 | 5.492 · USD 2.040.216 | **4.517 · USD 1.704.045** | −17,8 % · −16,5 % |
| Domingo | 37.377 | 4.669 · USD 1.765.184 | **3.899 · USD 1.474.580** | −16,5 % · −16,5 % |
| **Semana** | | USD 19.118.985 | **USD 16.265.970** | **−14,9 %** |

Semillas del día laboral: 7.351, 7.345 y 7.357 buses (USD 2.617.245, 2.616.061 y 2.619.101).

### 5.2 De dónde sale el ahorro (día laboral)

| Paso | Buses | USD/día |
|---|---|---|
| Caso base miope | 8.684 | 3.062.717 |
| Plan inicial del método (construcción cronológica) | 7.570 | 2.677.608 |
| + pares y tríos, 40 min (el método de la Entrega 2) | 7.433 | 2.639.411 |
| **+ cuartetos al azar, 40 min** | **7.351** | **2.617.469** |

Métodos comparados a 40 min en el día laboral (buses):

| Método | Buses |
|---|---|
| Pares | 7.524 |
| Pares + tríos | 7.433 |
| Tríos al azar | 7.374 |
| **Cuartetos al azar** | **7.351** |
| Quintetos al azar | 7.369 |
| Octetos al azar | 7.489 |
| Mezcla creciente | 7.520 |
| Cuartetos parecidos | 7.496 |

Lectura: elegir los buses al azar le gana a elegirlos parecidos, y el mejor tamaño de grupo es 4.

**Cuidado:** el −2,25 % (−4,80 % el sábado, −8,00 % el domingo) se mide contra el **plan inicial**, no
contra el caso base.

### 5.3 Qué tan cerca del óptimo

- **5 casos chicos** (2 a 4 rutas, 84 a 157 corridas): óptimo demostrado en todos, en 1 a 8 min cada
  uno. Brecha media al óptimo con 120 s de búsqueda:

  | Método | Brecha media |
  |---|---|
  | Plan inicial | 1,39 % |
  | Pares | 1,24 % |
  | Pares + tríos | 0,61 % |
  | Mezcla creciente | 0,56 % |
  | Tríos al azar | 0,15 % |
  | Quintetos y octetos al azar | 0,14 % |
  | **Cuartetos al azar** | **0,13 % (peor caso 0,31 %)** |

- **Casos más grandes con la exacta podada** (batería de 350 kWh):

  | Caso | Corridas | Óptimo | Cuartetos (5 min) |
  |---|---|---|---|
  | rutas_06 | 129 | 24 buses · USD 7.506,30 | sin correr |
  | rutas_08 | 200 | 38 buses · USD 11.517,04 | sin correr |
  | mediano_200 | 200 | 24 buses · USD 8.177,94 | +0,03 % |
  | **rutas_10** | **293** | **60 buses · USD 18.204,24** | **+0,57 %** |

- **Red completa:** no se puede demostrar el óptimo. La cota básica (6.601 buses en circulación a la
  vez más los km de servicio) es USD 2.322.956, y el plan queda 12,7 % sobre ella. Es una cota débil:
  ignora la recarga, los sectores y las plazas.
- Mensaje para el informe y el deck: **la solución es aproximada**, a menos de 1 % del óptimo donde se
  puede medir. Nunca decir que la solución de la red completa es «óptima».

### 5.4 Recarga forzada (baterías chicas)

Con 350 kWh casi ningún bus recarga. Por eso se probaron copias de los 5 casos chicos con baterías de
150 y 120 kWh. Con 100 kWh no alcanza: hay servicios que necesitan entre 105 y 112 kWh.

- La heurística mejora el plan inicial entre 6 y 27 % con 150 kWh, y entre 14 y 24 % con 120 kWh.
- Con recarga, la exacta **no demuestra el óptimo en 15 min**: su mejor plan queda entre 1,8 y 15,5 %
  sobre su cota.
- La mejor heurística queda, en promedio, +4,8 % (150 kWh) y +2,8 % (120 kWh) sobre el **mejor plan
  de la exacta**, que no es el óptimo.
- En el caso grande (bat150_rutas_10, 293 corridas), **la heurística le gana a la exacta corrida
  durante 1 h**: 62 buses y USD 19.625, contra 64 buses y USD 19.697.
- Dar 15 min en vez de 2 casi no cambia el resultado: la búsqueda se detiene sola, sin mejoras en el
  vecindario. La diferencia viene del vecindario, no del tiempo. Queda como trabajo futuro probar grupos
  que muevan recargas entre buses.

### 5.5 KPI (sobre el plan final de cuartetos, semilla 1; recalculados el 22-nov)

- Contra el caso base, día laboral: −15,4 % de buses (8.684 → 7.351), −14,5 % de costo y −30,4 % de
  km en vacío. Sábado: −17,7 % de buses y −16,4 % de costo. Domingo: −16,4 % y −16,4 %.
- **Los cargadores no son el cuello de botella.** En día laboral el pico es de 15 a 38 buses cargando a
  la vez por electroterminal (11 a 21 % de las conexiones), entre las 19:25 y las 19:55, al inicio del
  tramo caro. El caso base llena las conexiones de E2, E4 y E5 entre las 20:00 y las 22:00.
- **Las plazas se llenan solo al cierre.** Durante la operación se usa como máximo el 11 a 21 % de las
  plazas (41 % el sábado); al cierre, 700 buses quedan estacionados en los electroterminales.
- **Hay desbalance entre sectores.** El sector 3 (Los Espinos) carga solo el 37,6 % de su energía en su
  propio electroterminal; los demás, entre 56,5 % y 76,1 %.
- **La energía pesa el 0,4 % del costo.** Se compra solo el 2,5 % de la energía que se consume.

### 5.6 Repetibilidad: el límite más importante

Los buses parten llenos y terminan con unos 66 kWh en promedio (plan de cuartetos, día laboral). Para
repetir el día habría que reponer **2,08 GWh** de noche, lo que toma 16,5 h con las 700 conexiones a
180 kW (10,7 h el sábado y 9,1 h el domingo). Además, 6.651 de los 7.351 buses terminan en terminales
sin cargadores. **Con la
infraestructura actual, el plan no se puede repetir día tras día.** Se presenta como hallazgo; no se
esconde.

---

## 6. Mapa del repositorio

| Carpeta | Qué hay |
|---|---|
| `00-enunciado/` | Enunciado P7 y lineamientos de las tres entregas; para esta, manda `Lineamientos Entrega 3 2026-2.docx` |
| `01-datos/` | Datos del curso (GTFS, red vial, CSV). **No está en GitHub** (1,3 GB) |
| `02-analisis-datos/` y `03-resultados/` | Análisis de datos de la Entrega 1 y sus salidas |
| `04-documentos/` | Documentos de trabajo en LaTeX y PDF |
| `05-entrega1/` y `08-entrega2/` | Lo entregado. `08-entrega2/informe2/` es la plantilla del informe final |
| `09-entrega3/` | Todo lo de la entrega final (detalle abajo) |
| `codigo/` | Fase 1, tres fases y **caso base miope** (`tres_fases/caso_base.py`) |
| `metodo_hibrido/` | **Método principal**: construcción, grupos, MILP local, exacta y auditoría |
| `caso_base_simple_gurobi/` | Caso base sin recargas (histórico, de la Entrega 2) |
| `graphify-out/` | Grafo de conocimiento del repo, de la herramienta `graphify` (opcional) |

Dentro de `09-entrega3/`:

| Subcarpeta o archivo | Qué hay |
|---|---|
| `PLAN-ENTREGA3.md` | Plan maestro: rúbricas, decisiones D1–D8, tareas T0–T12, estructura del informe, banco de preguntas y checklist |
| `INFORME-RESULTADOS.md` | Todos los resultados, explicados para el grupo |
| `octetos/` | Estudio de tamaños de grupo, exacta y recarga forzada. Casos en `casos/`, resultados en `resultados/*.csv` |
| `kpi/` | KPI y uso de electroterminales (`kpi_planes.py`, `uso_electroterminales.py`, `ocupacion_plazas.py`) |
| `sensibilidad/` | `crear_escenarios.py`, que genera la instancia de cada escenario |
| `mapa_sectores/` | Mapa de sectores, informe simple y metodología en 2 páginas |
| `presentacion/` | `deck.html` (láminas 1–11), `presentacion_final_G29.pptx`, `ASIGNACION-LAMINAS-12-20.md` y `AUDITORIA-RUBRICA.md` |
| `figuras/` | GIF y pasos de la absorción (lámina 10) |
| `scripts/` | Auditoría del caso base |

**Lo que no está en GitHub:**
- `01-datos/`;
- las instancias completas (`metodo_hibrido/instancia_417*`);
- los planes bus por bus (`planes.json` y `actividades.csv`, de 20 a 50 MB cada uno), incluidos los de
  `octetos/resultados/planes_417_*`;
- los entornos de Python y las licencias.

Todo eso está en el Mac donde se corrió el proyecto. Hubo una carpeta de Drive con zips de datos y
corridas; su enlace está en el historial del README (commit `720ae79`) y se quitó el 19-nov. Para
conseguir datos o planes, hay que pedírselos a quien mantiene el repo (cuenta `nfariasl`).

---

## 7. Preparar el computador y correr

```bash
git clone https://github.com/nfariasl/capstone-buses-electricos.git
```

```bash
cd capstone-buses-electricos && python3 -m venv .venv-optimizacion
```

```bash
.venv-optimizacion/bin/pip install "gurobipy>=12,<13" numpy scipy pandas matplotlib pytest
```

- **Licencia de Gurobi.** La gratuita que viene con pip solo resuelve modelos de hasta 2.000 variables y
  2.000 restricciones. Alcanza para las pruebas y el caso base simple, pero **no** para tríos en
  adelante ni para la exacta. Cada persona necesita su licencia académica (`grbgetkey`, desde la red UC
  o con VPN).
- **Datos.** Copiar `01-datos/` en la raíz (hay que pedirla). `codigo/` usa enlaces simbólicos a
  `01-datos/`.
- **Instancia completa:** `python metodo_hibrido/preparar_completa.py --servicio L` (también S y D).
- **Estudio de métodos:** `bash 09-entrega3/octetos/correr_todo.sh`. Si se corta, retoma con
  `--continuar`.
- **KPI** (no necesita Gurobi): `python3 09-entrega3/kpi/kpi_planes.py`.
- **Pruebas:** usar el bucle de `README.md`, sección «Pruebas». Unas 192 pasan; algunas necesitan
  `01-datos/`. Las lentas corren con `PRUEBAS_LENTAS=1`.

**Equipo de referencia:** todo lo de la Entrega 3 se corrió en un Mac M1 de 8 GB. La exacta completa
con 200 corridas usó unos 13 GB y no cupo en memoria; la podada sí cabe. Con 4 hilos el Mac se calienta
mucho.

---

## 8. Decisiones ya tomadas (no reabrir sin hablarlo con el grupo)

| Decisión | Qué se decidió |
|---|---|
| Método final | **Cuartetos al azar con 40 min**; cifra principal: 7.351 buses (promedio de 3 semillas) |
| Regla de elección | El más barato con el mismo tiempo, sin umbral mínimo de mejora (11-nov) |
| Caso base | Miope por ruta con recarga, umbral 0 % (8.684 buses en día laboral) |
| Alcance | 417 rutas en L, S y D; semana = 5 L + S + D; flota = la del día laboral |
| Escenario energético | Día aislado con batería llena; la repetibilidad se analiza aparte |
| Sectores | Fijos; cada bus atiende un solo sector |
| Distancia al óptimo | Se mide en los 5 casos chicos y en los de 6 a 10 rutas que resolvió la exacta podada |
| Escalera de casos medianos (250–400 corridas) | Descartada por falta de memoria |
| Deck | Se itera en HTML → PPTX → Canva (diseño `DAHbqgcw7t8`); colores de RED; tipografías Overpass y Source Serif 4 |
| Vocabulario | «corrida» (no «viaje»), «electroterminal» (no «terminal») y «cuartetos al azar» para nuestro plan |

**Siguen abiertas:**
- quiénes exponen: máximo 3, y los 7 deben haber expuesto en alguna de las tres entregas;
- con qué semilla se calculan los KPI;
- si se cobra la espera.

---

## 9. Lo que falta, por prioridad

Cada tarea dice qué hay que hacer, con qué archivos y cuándo está terminada.

### A. Presentación final (urgente: alrededor del 24-nov, por confirmar)

**Estado.** `09-entrega3/presentacion/deck.html` tiene 11 láminas: portada, contexto, problema,
objetivo, datos, KPIs, caso base, método, sectores, absorción e implementación. Sus notas suman 7:20.
La versión que se edita está en Canva (`DAHbqgcw7t8`).

**Por hacer:**
1. **Láminas 12 a 20** en Canva. Seguir `ASIGNACION-LAMINAS-12-20.md`, que da para cada una el
   mensaje, los pasos, las cifras con su archivo de origen y qué evitar. Entre las nueve deben durar
   6:40 como máximo.

   | Lámina | Tema |
   |---|---|
   | 12 | Resultado del día laboral |
   | 13 | Sábado, domingo y semana |
   | 14 | De dónde sale el ahorro |
   | 15 | Distancia al óptimo |
   | 16 | Sensibilidad (espera los resultados de §9 C) |
   | 17 | Recarga forzada |
   | 18 | El día siguiente |
   | 19 | Conclusiones |
   | 20 | Implementación, piloto y limitaciones |

2. **Arreglos a las láminas 1 a 11**, según `AUDITORIA-RUBRICA.md`:
   - 3: definir «corrida»;
   - 5: título del eje vertical;
   - 7: peso de cada costo del caso base;
   - 8: debilidades del híbrido y equipo de cómputo;
   - 11 (implementación), el mayor riesgo: falta cómo reproducirlo, cuánto demora, en qué equipo y la
     lista de lo que los auditores no certifican.
3. **Anexos** para el banco de preguntas: MILP de recarga, por qué se descartaron las otras familias de
   métodos, sectores fijos, atrasos, 18 km/h, transformador, espera, tiempo y equipo, y cómo lo
   implementaría RED.
4. **Definir expositores** (decisión D7) y **ensayar 3 veces** con cronómetro, con meta de 14:00 a
   14:30. Si un ensayo se pasa, se corta contenido, empezando por la lámina 20; no se habla más rápido.

**Terminado cuando:**
- las 20 láminas están numeradas «n / 20»;
- cada gráfico tiene leyenda, ejes y unidades;
- las cifras son las mismas del informe;
- un ensayo completo cae dentro del tiempo.

### B. KPI sobre el plan de cuartetos — ✅ HECHO (22-nov, noche)

`planes.py` ya apunta a los planes de cuartetos, semilla 1; se corrieron `kpi_planes.py`,
`uso_electroterminales.py`, `ocupacion_plazas.py` (L, S y D) y las 9 pruebas, que pasan. Las cifras
están en §5.5 y en `kpi/resultados/`. Lo único pendiente es pasarlas a la lámina 14. Lo que sigue
queda como registro de cómo se hizo.

**Problema (resuelto).** Los KPI de `09-entrega3/kpi/` usaban el plan de 7.427 buses de octubre, y la
cifra principal es 7.351 (cuartetos). No mezclar cifras de dos planes en una misma lámina.

**Qué hacer:**
1. Elegir la semilla. Recomendación: **semilla 1** (7.351 buses, USD 2.617.245), que coincide con el
   promedio redondeado.
2. En `09-entrega3/kpi/planes.py`, **reemplazar** las tres líneas `('metodo', …)` de `PLANES` por:
   ```python
   ('metodo', 'L', '09-entrega3/octetos/resultados/planes_417_L/instancia_417_cuartetos_azar_s1_2400s'),
   ('metodo', 'S', '09-entrega3/octetos/resultados/planes_417_S/instancia_417_S_cuartetos_azar_s1_2400s'),
   ('metodo', 'D', '09-entrega3/octetos/resultados/planes_417_D/instancia_417_D_cuartetos_azar_s1_2400s'),
   ```
   Hay que mantener el nombre `metodo`: `kpi_planes.py` (línea 121) calcula el ahorro comparando
   `metodo_{día}` contra `caso_base_{día}`, y `uso_electroterminales.py` grafica solo esos dos nombres.
   Si se agregan líneas con otro nombre, el ahorro y las figuras siguen saliendo del plan de 7.427.
3. Correr `kpi_planes.py`, `uso_electroterminales.py`, `ocupacion_plazas.py` y sus pruebas.
4. Actualizar `kpi/README.md`, `INFORME-RESULTADOS.md` §7 y la lámina 14.

**Solo se puede hacer en el Mac donde están los planes**, porque no están en GitHub. Ojo: pueden estar
«solo en iCloud» (ver §10).

### C. Sensibilidad (40 pts del informe; lámina 16)

**Estado.** Los escenarios están definidos en `09-entrega3/sensibilidad/README.md`:

| Escenario | Cambio |
|---|---|
| Plazas −20 %, +20 % y +50 % | Plazas y conexiones de cada electroterminal |
| Mitad de conexiones | Mismas plazas |
| Cierre de cada electroterminal | Uno a la vez (5 escenarios) |
| Tarifa de punta +50 % | Precio de los tramos de punta × 1,5 |
| Plazas según demanda | Las 700 plazas repartidas según las corridas de cada sector |

**No hay resultados en el repo.** Puede que se estén corriendo en el Mac principal: **preguntar antes de
duplicar el trabajo**.

**Qué hacer:**
1. Crear las instancias:
   ```bash
   python3 09-entrega3/sensibilidad/crear_escenarios.py --instancia metodo_hibrido/instancia_417 --destino metodo_hibrido/sensibilidad_417_L
   ```
2. Correr cuartetos al azar en cada escenario con `09-entrega3/octetos/correr_metodos.py --instancias ...`.
   Con 40 min por escenario son unas 8 h para los 11. Con 10 min (600 s) también sirve, pero hay que
   compararlos contra la instancia base corrida con el **mismo** presupuesto y en el **mismo** equipo.
3. Medir con `kpi/` y graficar el costo de cada escenario (y un gráfico de tornado, si alcanza).
4. **Limitaciones que hay que declarar:**
   - el caso base no lee `escenario.json`, así que no se puede comparar contra él en cada escenario sin
     modificar `codigo/tres_fases/caso_base.py`;
   - consumo, batería, velocidad en vacío, potencia y costos por bus y por km están fijos en el código.

**Terminado cuando:** hay una tabla con buses, costo y Δ % de cada escenario contra el escenario base, con
la justificación de cada parámetro y lo que implica para RED.

### D. Repetibilidad e infraestructura (lámina 18; tarea T7 del plan)

**✅ Hecho el 22-nov (noche)** con `09-entrega3/kpi/repetibilidad.py` (3 pruebas en
`test_repetibilidad.py`). Salida: `kpi/resultados/repetibilidad.csv` y `.md`, para los 6 planes.

Cada bus se recarga en el electroterminal de su sector, en su ventana nocturna (de su última llegada a su
primera salida, que se repite igual). Plan de cuartetos:

| Día | Energía a reponer | Se alcanza a entregar | MW necesarios / instalados | Conexiones necesarias / hay |
|---|---|---|---|---|
| Laboral | 2.085 MWh | 45 % | 278 / 126 | 1.547 / 700 (faltan 847) |
| Sábado | 1.351 MWh | 75 % | 163 / 126 | 909 / 700 (faltan 230) |
| Domingo | 1.150 MWh | 90 % | 126 / 126 | 704 / 700 (faltan 76) |

- La ventana nocturna mediana es de 7,5 h en día laboral (8,3 h el sábado y 9,2 h el domingo).
- En día laboral faltan conexiones en los 5 electroterminales. El peor es E5 Santa Rosa (38 % cubierto,
  faltan 246); el mejor es E1 Vespucio Norte (71 %, faltan 61).
- **El caso base tampoco se repite:** en día laboral cubre el 52 % y le faltan 656 conexiones. No es un
  defecto solo de nuestro método: los dos parten con la flota llena, como dice el enunciado.
- **Es una cota optimista.** Supone que todas las conexiones trabajan toda la ventana, que no hay límite
  de transformador y no cuenta el viaje en vacío hasta el electroterminal (6.651 buses terminan en
  terminales sin cargadores). La brecha real es al menos esta.

### E. Incertidumbre (T9; sin empezar)

Hacer un Monte Carlo sobre el plan fijo:
- variar las duraciones de las corridas (±10 a 20 %) y el consumo;
- medir las salidas atrasadas, el atraso medio y máximo, y los buses que bajan de la reserva de 35 kWh.

Lee `04_final/actividades.csv`, que no está en GitHub. Si no hay tiempo, se declara como limitación y
trabajo futuro.

### F. Informe final (200 pts, reprobatorio; alrededor del 27-nov, por confirmar)

**No hay nada escrito aún en el repo.** Lo que piden los lineamientos:
- máximo 45 páginas, sin contar portada, anexos ni bibliografía;
- LaTeX, Times New Roman 11, el documento base del curso sin modificar e índice;
- **abstract en inglés** y **resumen ejecutivo**;
- decir si la solución es óptima o aproximada, con evidencia;
- análisis de incertidumbre y análisis crítico;
- **propuesta de implementación con piloto** y cómo medir su éxito;
- declaración de IA firmada por los 7.

**Estructura propuesta** (`PLAN-ENTREGA3.md` §8):

| Cap. | Contenido | Págs. |
|---|---|---|
| — | Abstract y resumen ejecutivo | 1,5 |
| 1 | Introducción | 1,5 |
| 2 | Problema y KPIs | 3,5 |
| 3 | Datos | 3,5 |
| 4 | Bibliografía y evolución metodológica | 4 |
| 5 | Modelo y supuestos | 4 |
| 6 | Estrategia e implementación | 4,5 |
| 7 | Caso base | 2 |
| 8 | Resultados | 8 |
| 9 | Sensibilidad, incertidumbre y repetibilidad | 6 |
| 10 | Implementación y piloto | 2,5 |
| 11 | Conclusiones | 2 |

Anexos: notación; **correcciones** (cada comentario recibido y dónde se atendió); parámetros de los
escenarios; tablas de sensibilidad; cómo reproducir los resultados.

**Cómo armarlo:**
1. Copiar el pipeline de `08-entrega2/informe2/` (`compilar.sh`, `scripts/cifras.py`, `figuras.py`,
   `revisar.py` y la plantilla `pucthesis.cls`) a `09-entrega3/informe3/`.
2. Hacer que `cifras.py` lea los CSV de la Entrega 3 y genere las macros. **Ninguna cifra se escribe a
   mano.**
3. Reutilizar texto del informe 2 (capítulos 2, 3, 4 y 7) y de `mapa_sectores/metodologia.tex`.
4. Para Overleaf, subir un zip con `cifras.tex` y las figuras ya generadas, porque Overleaf no corre
   Python.
5. Atender los comentarios recibidos:
   - la corrección anotada del informe 1 (13 comentarios);
   - el feedback de la presentación del 8-oct;
   - la corrección del informe 2, cuando llegue;
   - la retroalimentación de pares.

   Guardarlos en `09-entrega3/comentarios/`, que todavía no existe.

**Rúbrica:** abstract 5 · resumen e introducción 5 · problema 15 · modelo y metodología 60 ·
resultados 50 · sensibilidad y extensiones 40 · conclusiones 25.

### G. Corridas que quedaron sin hacer (opcional)

- La exacta de rutas_12 (442 corridas; se cortó a los 34 min).
- Las heurísticas de rutas_06, rutas_08 y rutas_12.
- Los medianos de 250 a 400 corridas, que necesitan un computador con más de 16 GB. Las instrucciones
  están en `octetos/INSTRUCCIONES-EXACTA-MEDIANOS.md`.
- Más réplicas para medir la variabilidad (T6).

Solo si sobra tiempo.

### H. Repositorio final y trámites

- Poner la etiqueta `entrega-3` en el commit que calce con el informe, y el enlace al repo en el
  informe.
- Dejar en el README una orden por resultado (está casi listo).
- Firmar entre los 7 la declaración de IA.
- Responder todos la **evaluación de pares**: a quien no la responde, se le multiplica la nota por 0,75.

---

## 10. Reglas y trampas conocidas (leer antes de tocar código o cifras)

1. **No inventar cifras.** Cada número sale de un archivo del repo y se dice de cuál. Si dos fuentes no
   calzan, gana el informe y se avisa al grupo.
2. **Cifras que se confunden:**
   - Las buenas son 64.502 corridas, 417 rutas y 6.601 buses, no 64.603, 418 y 6.603.
   - 7.351 (cuartetos, la cifra principal y base de los KPI desde el 22-nov) no es 7.427 (plan de octubre), ni
     7.433 (pares y tríos de noviembre), ni 7.570 (plan inicial).
   - El −2,25 % es contra el plan inicial; contra el caso base, el costo baja 14,5 %.
   - Con recarga forzada, «heurística contra exacta» se mide contra el **mejor plan conocido**, no
     contra el óptimo.
3. **La búsqueda se corta por reloj**, así que los resultados dependen del equipo. El Mac M1 es unas
   6,6 veces más rápido que el Windows del ensayo de octubre. Solo se comparan corridas hechas en el
   mismo equipo.
4. **No modificar a la ligera los `metodo_hibrido/*.py` de primer nivel.** `ejecutar.py` guarda la
   huella SHA-256 de cada módulo en cada corrida, y un cambio rompe la trazabilidad. Los scripts nuevos
   van fuera de esa carpeta, como en `08-entrega2/sensibilidad_presupuesto/` o `09-entrega3/`.
5. **Los parámetros físicos están fijos en el código.** Batería y reserva se pueden cambiar con las
   variables de entorno `BATERIA_KWH` y `RESERVA_KWH` (`metodo_hibrido/energia.py`), y `load_instance`
   rechaza un caso cuyo `escenario.json` declare otra batería. Lo demás (consumo, velocidad, potencia,
   costos) hay que cambiarlo en el código.
6. **La exacta usa un margen numérico:** `exacto.py` tiene `MARGEN_KWH = 1e-3`. Sin él, el auditor
   rechazaba planes con 34,9999 kWh.
7. **Los logs de la cola mienten.** `noche.log` y `recarga_15min.log` dicen «código 0» en todas las
   etapas. Para saber si una etapa terminó, hay que ver si dejó filas en el CSV.
8. **Nombres de carpeta:** `codigo/` antes se llamaba `CODIGO apstone/`, y `02-analisis-datos/` era
   `02-codigo/`. El código acepta los dos nombres; los PLAN*.md viejos usan los antiguos.
9. **iCloud:** la carpeta original vive en iCloud, que a veces deja archivos solo en la nube y las
   lecturas se cuelgan. Se detecta con `ls -lO` (aparece `dataless`) y se arregla con «Mantener
   descargado». En un clon fuera de iCloud no pasa.
10. **La API de Canva** no aplica transiciones, tipografías ni espaciado: eso se hace a mano.
11. **Estilo de las láminas:**
    - una cifra grande y una frase corta, con el detalle en las notas;
    - cada cifra aparece una sola vez en el deck;
    - ningún porcentaje sin su referencia;
    - todo gráfico con leyenda y unidades.
12. **Commits:** en español, con el formato `tipo: descripción` (feat, fix, docs, chore, refactor…).

---

## 11. Glosario

| Término | Significado |
|---|---|
| Corrida | Un viaje programado de una ruta, con hora y terminal de salida y de llegada |
| Jornada | Lo que hace un bus en el día: sus corridas, traslados en vacío, recargas y estacionamiento final |
| Cadena | Secuencia de corridas que un mismo bus puede hacer una tras otra (Fase 1) |
| Traslado en vacío (*deadhead*) | Km sin pasajeros entre corridas o hacia un electroterminal |
| Electroterminal (E1–E5) | Depósito con cargadores; también sirve de estacionamiento |
| Sector | Grupo de rutas asignado a un electroterminal |
| Caso base miope | Cada ruta con sus propios buses, que recargan al 100 % cuando no les alcanza |
| Plan inicial | Resultado de la construcción cronológica, antes de la mejora local |
| Pares, tríos, cuartetos, quintetos, octetos | Tamaño del grupo de jornadas que se reoptimiza junto (2, 3, 4, 5 u 8) |
| Al azar / parecidos | Cómo se eligen los buses del grupo: con una semilla, o por horarios similares |
| MILP local (`conjunta.py`) | Modelo entero que decide recargas y terminales de las jornadas del grupo |
| Exacta / exacta podada | MILP del problema completo para casos chicos. La podada quita las recargas dominadas y las capacidades, que el auditor revisa después |
| Brecha | Cuánto más caro es un plan que el óptimo o que una cota, en % |
| Cota | Piso de costo que ningún plan factible puede bajar |
| Semilla | Número que fija el azar para poder repetir una corrida |
| Presupuesto | Segundos de reloj de búsqueda (2.400 s = 40 min) |

---

## 12. Preguntas probables del jurado (respuesta corta)

- **¿La solución es óptima?** No, es aproximada: a 0,13 % del óptimo en los 5 casos chicos y a 0,57 % en
  el de 293 corridas. En la red completa queda 12,7 % sobre una cota débil.
- **¿Cómo se repite el día siguiente?** Hoy no se repite solo: faltan 2,08 GWh, que toman 16,5 h de carga
  nocturna con las 700 conexiones. Es un hallazgo, con una recomendación de infraestructura.
- **¿Por qué no respetan los 1.200 buses declarados?** Cubren alrededor del 28 % del servicio. El tamaño
  de la flota es la decisión, no un dato.
- **¿Por qué sectores fijos?** Achican el problema. En el 26 % de las rutas el segundo electroterminal
  queda a menos de 5 % de distancia del primero, así que liberar los sectores es una extensión natural.
- **¿Y el límite del transformador?** El dato no viene; se modeló como conexiones × 180 kW. Va como
  sensibilidad o como limitación.
- **¿Por qué no cobran la espera?** Sumaría unos USD 21 a 22 mil al día a ambos planes (medido en la
  muestra de 212 rutas), así que no cambia la comparación.
- **¿Cuánto demora y en qué equipo?** 40 min de búsqueda por tipo de día en un Mac M1 de 8 GB, más la
  construcción inicial.
- **¿Qué pasa con baterías más chicas?** Ver §5.4: el método sigue funcionando y queda a 0–7 % del mejor
  plan conocido.

---

## 13. Índice de documentos detallados

| Si tu tarea es… | Lee |
|---|---|
| Entender todos los resultados | `09-entrega3/INFORME-RESULTADOS.md` |
| Planificar o revisar la rúbrica | `09-entrega3/PLAN-ENTREGA3.md` y `00-enunciado/Lineamientos Entrega 3 2026-2.docx` |
| Hacer las láminas 12–20 | `09-entrega3/presentacion/ASIGNACION-LAMINAS-12-20.md` |
| Arreglar las láminas 1–11 | `09-entrega3/presentacion/AUDITORIA-RUBRICA.md` |
| Recarga forzada y exacta podada | `09-entrega3/octetos/INFORME-COLA-NOCTURNA.md` |
| Tamaños de grupo (pares a octetos) | `09-entrega3/PLAN-PARES-TRIOS-OCTETOS.md` y `09-entrega3/octetos/INVESTIGACION.md` |
| KPI | `09-entrega3/kpi/README.md` y `09-entrega3/kpi/resultados/kpi_planes.md` |
| Sensibilidad | `09-entrega3/sensibilidad/README.md` |
| Sectores y metodología en lenguaje simple | `09-entrega3/mapa_sectores/informe_sectores.pdf` y `metodologia.pdf` |
| Método híbrido (código) | `metodo_hibrido/README.md` y `metodo_hibrido/RESULTADOS.md` |
| Caso base | `codigo/tres_fases/CASO_BASE.md` |
| Fase 1 y modelo matemático | `codigo/fase1/MODELO_MATEMATICO.md` y `codigo/README.md` |
| Auditorías y lo que no certifican | `metodo_hibrido/revision_auditorias_20261006/AUDITORIAS_Y_CAMBIOS.md` |
| Informe 2 (plantilla y texto reutilizable) | `08-entrega2/informe2/` (`informe2.pdf`, `ESQUEMA.md` y `PLAN.md`) |
| Instalar y correr | `README.md` |
