# Informe final — estado del trabajo (pausado el 25-nov-2026, tarde)

La usuaria pidió armar el informe final completo de una vez («tenemos todo el contexto, presentación,
lee todo eso y armalo ya») y luego pausar. Este archivo dice qué está hecho y qué falta, para retomar.

## Hecho

- Carpeta `09-entrega3/informe3/` con la plantilla del curso copiada del informe 2 (`pucthesis.cls` a
  11 pt, `apacite`, `referencias.bib`, `figures/LogoUC.pdf`).
- `scripts/fuentes.py`: rutas a los resultados de la Entrega 3 y lectura (avisa si un archivo está solo
  en iCloud; se bajaron con `brctl download` las corridas de `metodo_hibrido/instancia_417_S` y `_D`).
- `scripts/cifras.py`: **605 macros** en `cifras.tex` y 10 tablas en `tablas/` (métodos en la red
  completa, brecha en casos chicos, casos de 6–12 rutas, recarga forzada, sectores, sensibilidad, físicos,
  costos, atrasos, repetibilidad). Reutiliza las macros del informe 2 con prefijo `Edos`. Cifras
  comprobadas contra `CONTEXTO-DEL-PROYECTO.md` (7.351 buses, −14,5 %, semana −14,9 %, brecha 0,13 %,
  peor 0,31 %, cota 12,7 %, recarga forzada +4,8 / +6,8 %, etc.).
- `scripts/figuras.py`: 7 figuras PDF en `figures/` (corridas en curso L/S/D, ahorro por componente,
  tamaño de grupo, energía por hora, buses cargando a la vez, sensibilidad, atrasos). Paleta validada:
  plan = azul `#2a78d6`, caso base = naranja `#eb6834`, tercero = aqua `#1baf7a`. Revisadas a ojo; se
  corrigieron solapes de etiquetas.
- Copiadas a `figures/`: `mapa_sectores.pdf` y `absorcion_pasos.png` (dibujo de la operación, lo pidió
  la corrección del informe 2).

## Insumos leídos (no hace falta releerlos enteros)

- Informe 2 entregado y **corregido** (llegó hoy): `~/Downloads/annotated-PLANIFICACI…GRUPO_29 (1).pdf`,
  45 págs. Trae el texto de Overleaf (cap. 1–3, 5 con el MILP local completo, ec. 5.1–5.21, anexos A–C).
- Corrección del informe 2 (comentarios del ayudante), a atender y listar en el anexo de correcciones:
  1. Terminales comunes con capacidad ilimitada: ¿cómo afecta?, ¿y con una capacidad realista?
  2. ¿Se va a escalar a la red completa y cuánto cuesta? (ya resuelto: red completa L/S/D).
  3. Falta justificar mejor la metodología elegida.
  4. Hacer un diagrama de la metodología y del caso base (entradas, salidas, pasos) y ponerlo arriba.
  5. «Route first, charge second»: ¿qué tan bueno o malo es?, ¿algún estudio?
  6. Reestructurar: confunde que «aumenten los buses al incorporar la electricidad» como si fuera una
     decisión y no una obligación.
  7. «Basado en qué» combinan construcción cronológica y mejora local (citar literatura).
  8. Del costo del caso base, ¿qué es lo más mejorable? (flota ≈ 71 %).
  9. Confuso cómo se relaciona la metodología con el diagnóstico de la sección 3.2.
  10. Hacer dibujos de las operaciones (absorción, rotación).
  11. ¿Para qué es el MILP? Cuesta seguir el hilo.
  12. Poner el diagrama de flujo (sin código) más arriba, para entender el método completo.
- Corrección del informe 1: `~/Downloads/g29 anotado (1).pdf` (13 comentarios: definir corrida, siglas,
  objetivo completo, «distancia de qué», gráfico de corridas por hora, KPI contra caso base y no metas,
  «costo total» y «costo energético», terminales convencionales, carga lineal).
- Deck final (texto extraído de `presentacion/deck.html`, láminas 1–21 y anexos A1–A7) y
  `INFORME-RESULTADOS.md`, `04-documentos/discusion_metodologica.tex` (seis familias), lineamientos E3.

## Estructura acordada (PLAN-ENTREGA3.md §8, 45 págs. de cuerpo)

Abstract (inglés) y resumen ejecutivo · 1 Introducción · 2 Problema y KPIs · 3 Datos · 4 Revisión
bibliográfica y evolución metodológica · 5 Modelo formal (MILP de conexiones de `metodo_hibrido/exacto.py`)
y supuestos · 6 Estrategia de solución e implementación · 7 Caso base · 8 Resultados · 9 Sensibilidad,
incertidumbre y repetibilidad · 10 Implementación y piloto · 11 Conclusiones. Anexos: notación, correcciones
(informe 1, presentación 2, informe 2), MILP local completo, parámetros, tablas completas, reproducción,
declaración de IA.

Referencias a agregar a `referencias.bib`: Olsen, Kliewer y Wolbeck (2022), Alvo, Angulo y Klapp (2021),
Ahuja et al. (2002), Limmer, Varga y Raidl (2023) (fichas en `octetos/INVESTIGACION.md` y en el informe 2).

## Estado al 25-nov (noche)

Borrador completo. `./compilar.sh` genera cifras (649 macros), tablas, 8 figuras y `informe3.pdf`, y el revisor
pasa sin errores (cuerpo de 44 de 45 páginas; rechaza dos puntos en la prosa, negritas, «viaje» y cifras a mano).
`informe3_overleaf.zip` compila en una carpeta limpia. Redacción sin dos puntos ni negritas, a pedido de la usuaria.

Auditado el 25-nov (noche): cifras y afirmaciones contrastadas con los CSV y las fuentes; correcciones listadas en
`CONTEXTO-DEL-PROYECTO.md` §3.3, ítem 15. Piloto propuesto en Vespucio Norte con Los Espinos como control.

## Falta (lo hace el grupo)

1. Leer el borrador completo y corregir lo que no les suene propio.
2. Completar en la declaración de IA (anexo F) las herramientas que usó cada integrante y firmarla.
3. Confirmar la fecha de entrega en Canvas, poner la etiqueta `entrega-3` en el commit y subir el PDF.
