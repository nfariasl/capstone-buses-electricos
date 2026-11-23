# Auditoría del deck contra la rúbrica (22-nov-2026)

**Qué se revisó:** texto y notas de las láminas 1 a 11 en `deck.html`, contra los «Lineamientos informe y presentación 3 (final)», el plan (`PLAN-ENTREGA3.md`, sección 9) y los comentarios del 8-oct ligados en `08-entrega2/informe2/ESQUEMA.md`.
**Qué no se revisó:** no se miraron las capturas renderizadas, ni la versión de Canva (DAHbqgcw7t8), ni las láminas 12 a 20, que no existen todavía.

Rúbrica de la presentación (60 pts): problema 10 · datos 5 · KPIs 4 · caso base 5 · metodología 8 · implementación 5 · resultados 18 · cierre 5. Descuentos: comentarios del ciclo 2, elementos mal explicados o sin leyenda, estructura, dinámica y tiempo.

## Resumen por bloque

| Bloque (pts) | Láminas | Veredicto |
|---|---|---|
| Problema (10) | 2–4 | Cubierto. Falta el impacto y la escala de RED, y definir «corrida». |
| Datos (5) | 5 | Bien. Falta el título del eje vertical y reutilizar el 6.601 como cota. |
| KPIs (4) | 6 | Cubierto. Falta mostrar sus valores en los resultados. |
| Caso base (5) | 7 | Bien. Falta el peso de cada costo en el caso base. |
| Metodología (8) | 8–10 | Bien. Faltan debilidades del híbrido, el MILP y la evolución parejas, tríos y cuartetos. |
| Implementación (5) | 11 | **Riesgo.** Es una afirmación sin detalle; falta cómo reproducirlo. |
| Resultados (18) | 12–18 | Sin hacer. Es el 30 % de los puntos. |
| Cierre (5) | 19–20 | Sin hacer. Debe traer piloto, limitaciones y pasos siguientes. |

## Hallazgos por lámina

**1. Portada.** Sin número de lámina; los lineamientos piden numeración. Riesgo bajo. Aparecen los 7 integrantes.

**2. Contexto.** Separa contexto de problema, como pidió el feedback. El ejemplo está marcado como ilustrativo. Falta el «impacto» que pide la rúbrica: la escala de RED (cuántos buses eléctricos y cuántos viajes) no aparece en ninguna lámina.

**3. Problema.** «Corrida» no se define en la lámina. El feedback pidió definir corridas, cadenas, traslados en vacío y jornadas. Además, la lámina 3 usa «corrida» y las láminas 5 y 10 usan «viaje» (comentario A-p16 del informe 1). Elegir un término y definirlo una vez.

**4. Objetivo.** El 70,2 % se dice «en nuestro plan» antes de presentar el plan, y no dice de qué plan sale (cuartetos al azar, 2400 s). Poner el origen en la lámina o en las notas. La frase cita archivos (`parameters.csv`, `electricity_prices.csv`), que no se entienden desde afuera; basta «del enunciado».

**5. Datos.** Es la lámina más sólida. El Real / Enunciado / Supuesto separa bien lo que viene de los datos. Pendientes:
- El eje vertical no tiene título ni unidad. La frase de arriba lo explica, pero «elementos auto-explicativos» descuenta.
- Promete usar el 6.601 «para medir qué tan bueno es el nuestro». Esa cota debe aparecer en los resultados.
- Confirmar que el 6.601 coincide con el informe; en la Entrega 1 hubo un choque de cifras con 6.603 y 6.629.

**6. KPIs.** Los seis se comparan contra el caso base. «Energía al cerrar el día» promete mostrar si el día siguiente se repite; los resultados deben responder esa pregunta (feedback: «¿cómo se cubre el día siguiente?»).

**7. Caso base.** Incluye la recarga (pedido del feedback) y justifica el umbral más favorable. Falta el peso de cada costo en el caso base: el feedback pidió la composición del costo y hoy solo se da el 70,2 % del plan propio.

**8. Método.** Dice con honestidad que el híbrido no garantiza el óptimo (los lineamientos exigen decir si es óptimo o aproximado). Falta:
- Por qué se descartó cada una de las seis familias; hoy solo se nombran.
- Debilidades del híbrido más allá de «sin garantía».
- El equipo donde se miden los 40 min (pregunta probable del banco).

**9. Sectores y construcción.** El criterio de sectores es claro (menos km en vacío). El feedback pidió justificar sectores y rutas, y falta decir si fijar los sectores afecta el resultado. No aparece la exploración parejas, tríos, cuartetos y octetos, que es lo «creativo» que piden los lineamientos. Puede ir en los resultados.

**10. Absorción.** Buena. Tiene leyenda y está marcada como ilustrativa. Nunca se muestra el MILP de recarga, ni siquiera en un anexo.

**11. Implementación.** Es el riesgo principal (5 pts). El título afirma que todo fue auditado, pero la rúbrica pide el detalle de procedimientos y decisiones técnicas. Falta el enlace o la etiqueta `entrega-3` del repositorio, cuánto demora y en qué equipo. Los propios auditores declaran lo que no certifican (turnos, transformador, reposición, terminales finitos, espera, óptimo global, en `metodo_hibrido/revision_auditorias_20261006/AUDITORIAS_Y_CAMBIOS.md`). Un jurado puede cuestionar el título si esa lista no aparece, aunque sea en una línea.

## Transversales

- **Anexos:** el deck no tiene ninguno y el plan los pide para el banco de preguntas. Candidatas: MILP de recarga, descartes de las seis familias, límite del transformador, atrasos, 18 km/h en vacío, por qué sectores fijos.
- **Tiempo:** las notas de las láminas 1 a 11 suman 440 s (7:20). Para quedar en 14:00–14:30 quedan unos 6:40–7:10 para 9 láminas, o sea unos 45 s por lámina. Es ajustado, sobre todo con dos cambios de expositor.
- **Comentarios del ciclo 2:** no hay una lista que ligue cada comentario del feedback a una lámina. `09-entrega3/comentarios/` no existe. El ESQUEMA del informe 2 los liga solo con capítulos del informe, no con láminas.
- **Expositores:** hay que definir quiénes aún no han presentado, porque los 7 deben presentar en alguna de las tres entregas. Esto sigue abierto (decisión D7 del plan).

## Lo que deben cubrir las láminas 12 a 20 según los lineamientos

1. Si la solución es óptima o aproximada, con evidencia y cota (usar el 6.601 y la exacta en los 5 casos chicos).
2. Variabilidad entre réplicas, no solo el promedio de 3 semillas.
3. Comparación contra el caso base en cada KPI, con el Δ y el Δ %.
4. Sensibilidad con justificación de por qué esos parámetros, y qué implica cada cambio (lámina 16).
5. Respuesta al «día siguiente» (recarga forzada, bat150 y bat120).
6. Implementación: piloto por etapas y cómo se mide su éxito.
7. Limitaciones, qué se haría mejor y extensiones.
