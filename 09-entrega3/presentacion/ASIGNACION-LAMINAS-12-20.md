# Láminas 12 a 20: qué debe tener cada una

> **Desactualizado (23-nov).** El deck tiene ahora 21 láminas: 12–14 son de método (las del grupo), 15 resultado, 16 ahorro, 17 óptimo, 18 casos medianos y recarga forzada, 19 sensibilidad, 20 día siguiente y 21 conclusiones. Todas están armadas en `deck.html`. Lo que falta está en `AUDITORIA-OMISIONES.md`.


Guía para quienes arman estas láminas en Canva (diseño DAHbqgcw7t8). Las láminas 1 a 11 ya están hechas; copien su estilo. El HTML (`deck.html`) sirve de modelo.
Las cifras se calcularon el 22-nov-2026 desde los resultados del repo. Si una cifra no calza con el informe, gana el informe y se avisa.

## Reglas para todas

**Presupuesto de tiempo.** Las láminas 1 a 11 usan 7:20. Estas nueve deben sumar 6:40 como máximo, para terminar en 14:00–14:30 de los 15:00 que dan. Las notas llevan los segundos entre paréntesis al inicio, como en las demás, y un `[→]` por cada paso.

**Forma.**
- Una cifra grande y una frase corta. Nada de viñetas largas; el detalle va en las notas.
- Cada lámina avanza por 2 a 4 pasos. En Canva, cada paso es una página con la transición Match and move.
- Número de lámina «n / 20» y el encabezado del curso, igual que las anteriores.
- Todo gráfico lleva leyenda, título de ejes y unidades (descuenta si falta).
- Cada cifra se muestra una sola vez en el deck. Se pueden repetir solo 8.684 (caso base, lámina 12) y 6.601 (cota, lámina 15).
- Ningún porcentaje sin decir contra qué se compara y de dónde sale.

**Colores y tipografía** (de RED).

| Uso | Color |
|---|---|
| Nuestra solución | azul #0D5DAB |
| Caso base | gris #888B8D |
| Lo que se elimina | rojo #CF152D |
| Recarga | verde #16936A |
| Fondo | gris claro #F3F4F4 |

Títulos y cifras en Overpass; frase corta en Source Serif 4. Los íconos están en `presentacion/iconos/` (SVG) y `presentacion/exportacion/iconos/` (PNG).

**Vocabulario.** Usar «corrida» (un viaje programado de una ruta) y «electroterminal»; no «viaje» ni «terminal». Referirse siempre a «nuestro plan» como «cuartetos al azar».

**Cada lámina debe poder entenderse sin el orador**: sin siglas sin explicar y sin nombres de archivo.

## Cambios de expositor

Quedan donde el deck ya los tiene: en la lámina 8 y en la 14, con barrido rojo. Entonces las láminas 12 y 13 las expone quien venía de la 8, y de la 14 en adelante entra la tercera persona. Los nombres siguen sin asignar (decisión D7 del plan). Recuerden que los 7 deben haber presentado en alguna de las tres entregas.

---

## 12 · Resultado del día laboral · 45 s

**Mensaje:** con el mismo servicio, nuestro plan usa menos buses y cuesta menos que el caso base.
**Pasos:**
1. La barra gris del caso base (8.684 buses). Es la de la lámina 7, ahora achicada a escala.
2. La barra azul de nuestro plan, 7.351 buses (promedio de 3 semillas), con la diferencia en rojo: −1.333 buses (−15,4 %).
3. El costo diario: USD 3.062.717 contra USD 2.617.469, o sea −USD 445.248 (−14,5 %).

**Cifras desde:** buses y costo de nuestro plan, `octetos/resultados/red_completa_417_L.csv` (cuartetos al azar, 2400 s, promedio de las 3 semillas). Caso base, `kpi/resultados/kpi_planes.md`.
**Debe aclarar:** «Δ %» siempre contra el caso base, nunca contra el plan inicial. Confirmar que ambos costos usan la misma definición (decisión D2, la espera de 0,03 USD/min).
**Evitar:** el −2,25 %. Ese número es contra nuestro propio plan inicial, no contra el caso base.

## 13 · Sábado y domingo · 45 s

**Mensaje:** el resultado se repite en los tres tipos de día.
**Pasos:** el mismo par de barras (caso base gris, plan azul) para sábado y para domingo; después, el total de la semana.
**Cifras desde:** `red_completa_417_S.csv` y `red_completa_417_D.csv` para nuestro plan (S: 4.517 buses; D: 3.899 buses, promedios de 3 semillas); caso base, `kpi/resultados/kpi_planes.md` o las carpetas `codigo/output/tres_fases/red_417_{S,D}_caso_base/`.
**Debe incluir:** la semana (5 × laboral + sábado + domingo) y que la flota necesaria es la mayor de las tres, es decir, la del día laboral. Así se cumple el alcance prometido en la lámina 4.
**Pendiente de dato:** el caso base de S y D y el costo semanal; hay que sacarlos del archivo y verificarlos.

## 14 · De dónde sale el ahorro · 40 s · cambio de expositor, con barrido rojo

**Mensaje:** ahorramos buses, no energía.
**Pasos:**
1. Composición del costo en el caso base y en nuestro plan (buses, km, energía, sesiones), con el Δ y el Δ %.
2. Kilómetros en vacío y energía cargada, contra el caso base.
3. Uso de los electroterminales a lo largo del día: ¿los cargadores son un cuello de botella?

**Cifras desde:** `kpi/resultados/kpi_planes.md`, `uso_e_perfil_L.png` y `uso_e_mapa_calor_L.png`.
**Debe responder (feedback del 8-oct):** «peso de cada costo», «en qué horarios cargan los buses», «si el caso base carga, ¿sería tan grande la diferencia?».
**Hallazgos de KPI (plan de cuartetos, semilla 1; recalculados el 22-nov):** contra el caso base, −15,4 % de buses, −14,5 % de costo y −30,4 % de km en vacío. El pico de carga simultánea es de 15 a 38 buses por electroterminal, entre 11 % y 21 % de las conexiones, entre las 19:25 y las 19:55. Las plazas se usan como máximo al 21 % durante la operación y se llenan solo al cierre. La energía pesa 0,4 % del costo.
**Dependencia resuelta:** `kpi/resultados/` ya está calculado sobre el plan de cuartetos (semilla 1, 7.351 buses). Usar solo esas cifras; las del plan de 7.427 ya no van.

## 15 · Qué tan cerca del óptimo estamos · 50 s

**Mensaje:** el método es aproximado, pero medimos cuánto se aleja del óptimo.
**Pasos:**
1. Por qué no se puede probar el óptimo en la red completa (lámina 8) y qué hicimos: resolver al óptimo los 5 casos chicos (2 a 4 rutas, 84 a 157 corridas; cada uno en 1 a 8 min).
2. La brecha media de cada método al óptimo, a 120 s: plan inicial 1,39 %; pares 1,24 %; pares y tríos 0,61 %; mezcla creciente 0,56 %; **cuartetos al azar 0,13 %** (peor caso 0,31 %); octetos y quintetos 0,14 %; tríos 0,15 %.
3. En la red completa, el día laboral: gana cuartetos al azar con 7.351 buses, contra 7.433 de pares y tríos a 40 min. Mostrar también la cota inferior de 6.601 buses de la lámina 5: el plan queda a +11,4 % de ese piso.

**Cifras desde:** `octetos/resultados/casos_chicos.csv` y `casos_chicos_exacta.csv`; `red_completa_417_L.csv`.
**Debe responder (rúbrica):** «óptimo o aproximado, con evidencia y cota». La cota de buses no incluye km ni energía: decirlo.
**Debe mostrar la variabilidad:** las 3 semillas como rango, no solo el promedio.
**Es la lámina de creatividad:** exploramos varios tamaños de grupo y elegimos con datos (decisión del 11-nov: gana el más barato con el mismo tiempo).
**Evitar:** decir «óptimo» de la red completa. Es una solución aproximada.

## 16 · Sensibilidad · 55 s

**Mensaje:** el ahorro se mantiene cuando cambian los supuestos.
**Pasos:**
1. Por qué esos parámetros: los que más pesan o que el enunciado no fija (plazas, cargadores, tarifa en punta, cierre de un electroterminal).
2. Gráfico del costo contra cada escenario, con el caso base al lado.
3. Qué implica: ¿cuánto vale una plaza más?, ¿qué pasa si se pierde un electroterminal?

**Cifras desde:** los escenarios de `sensibilidad/README.md` (`plazas_-20`, `plazas_+20`, `plazas_+50`, `conexiones_-50`, `cierre_E1` a `E5`, `tarifa_punta_+50`, `plazas_por_demanda`). Estos resultados los está corriendo la usuaria; esta lámina queda con el espacio reservado hasta que termine.
**Debe cubrir:** la justificación de los parámetros (5 pts), el gráfico (20 pts) y las implicancias, es decir, cuán robustas son las conclusiones (10 pts).
**Limitación a decir:** consumo, batería, velocidad en vacío, potencia y costo por bus no entran en estos escenarios porque están fijos en el código. Es una limitación honesta y va en la lámina 20.

## 17 · Cuando la batería obliga a recargar · 40 s

**Mensaje:** con una batería chica el método sigue funcionando.
**Pasos:**
1. El escenario: la batería baja de 350 a 150 y a 120 kWh, para forzar muchas recargas.
2. Nuestro plan contra el plan inicial y contra la exacta podada en 10 rutas.
3. La brecha contra la cota inferior que entrega la exacta.

**Cifras desde:** `octetos/resultados/recarga_bat150.csv`, `recarga_bat150_exacta.csv`, `recarga_bat120.csv` y `recarga_bat120_exacta.csv`.
**Cuidado:** la exacta podada corre 900 s y **no siempre cierra el óptimo** (columna `optimo = False`, motivo `estado_9`, o sea límite de tiempo). Lo correcto es reportar la brecha contra su cota, `cota_usd`, y no llamar «óptimo» a ese costo.
**Debe responder:** qué pasa si se cumple el supuesto de batería y qué pasa si no.

## 18 · ¿Se puede repetir el día siguiente? · 40 s

**Mensaje:** los buses terminan el día con poca batería, y eso hay que reponerlo de noche.
**Pasos:**
1. Los buses parten con la batería llena y terminan con ~66 kWh en promedio (plan de cuartetos, `kpi_planes.md`).
2. Para repetir el día habría que reponer ~2,08 GWh durante la noche (16,5 h con las 700 conexiones a 180 kW).
3. Qué capacidad tienen los 5 electroterminales de noche, y qué se recomienda.

**Cifras desde:** `kpi/README.md` («Primeros hallazgos»), `kpi_planes.md` y la columna `energia_final` de los KPI.
**Debe responder (feedback del 8-oct):** «¿cómo se cubre el día siguiente?».
**Cálculo por electroterminal (hecho el 22-nov):** `kpi/resultados/repetibilidad.md`. En día laboral, las 700 conexiones alcanzan a entregar el **45 %** de la energía en la ventana nocturna (mediana de 7,5 h): harían falta 278 MW contra 126 instalados, o 1.547 conexiones contra 700. El sábado se cubre el 75 % y el domingo el 90 %. El caso base tampoco se repite (52 % en día laboral). Es una cota optimista: no cuenta el viaje hasta el electroterminal ni el transformador. Decirlo como hallazgo y recomendación de infraestructura, no esconderlo.

## 19 · Conclusiones · 45 s

**Mensaje:** los hallazgos, en tres frases.
**Pasos:**
1. Se necesitan menos buses que con el caso base, en los tres tipos de día (con la cifra de la lámina 12).
2. El ahorro viene de los buses y no de la energía; los cargadores no son el cuello de botella en el día, pero la noche sí hay que mirarla (láminas 14 y 18).
3. Es una solución aproximada, a 0,13 % del óptimo en los casos que se pueden medir (lámina 15), y robusta a los supuestos que probamos (lámina 16).

**Debe vincular:** cada conclusión con su lámina de evidencia y con los objetivos de la lámina 4.
**Evitar:** cifras nuevas. Las conclusiones solo resumen.

## 20 · Implementación, limitaciones y pasos siguientes · 30 s

**Mensaje:** cómo se llevaría a la práctica y qué falta.
**Pasos:**
1. **Piloto por etapas** (propuesta del plan, R6, a acordar con el grupo): primero el plan corre en paralelo, sin operarse (modo sombra); después se opera un sector y se compara con otro de control.
2. **Cómo se mide el éxito del piloto:** buses usados, costo, atrasos y energía al cierre, contra el sector de control.
3. **Limitaciones:** tiempos de viaje fijos, sin tráfico ni mantenciones (lámina 5); el método es aproximado; sectores fijos; el límite del transformador no está en los datos; parámetros sin sensibilizar (consumo, batería, velocidad en vacío).
4. **Pasos siguientes:** mejorar la solución con más tiempo o intercambios entre sectores, sensibilizar los parámetros que faltan y simular atrasos.

**Debe incluir:** el cierre, con la oportunidad concreta de implementación o extensión (rúbrica: cierre, 5 pts).
**Tiempo:** es la más corta; si el ensayo se pasa, el contenido se corta aquí y no se habla más rápido.

---

## Anexos (fuera de los 15 minutos, para el banco de preguntas)

Cada una con una respuesta de 30 s si la preguntan. Candidatas:
- MILP de recarga (la lámina 10 lo menciona y nunca se muestra).
- Por qué se descartaron las seis familias de métodos.
- Por qué sectores fijos y cómo afecta al resultado.
- Atrasos y simulación.
- 18 km/h en vacío.
- Límite del transformador.
- Por qué no se cobra la espera.
- Cuánto demora y en qué equipo.
- Cómo lo implementaría la Red.

## Qué verificar antes de dar una lámina por terminada

- [ ] Todas las cifras salen del archivo indicado y coinciden con el informe.
- [ ] Cada gráfico tiene leyenda, título de ejes y unidades.
- [ ] La lámina se entiende sin el orador.
- [ ] La nota dice cuántos segundos dura.
- [ ] La suma de las nueve láminas no pasa de 6:40.
- [ ] Hay un anexo para cada pregunta previsible que la lámina abre.
