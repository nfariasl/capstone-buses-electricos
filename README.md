# Capstone ICS2122 · Grupo 29 — Buses eléctricos en Santiago

Problema P7: programar la operación diaria de los buses eléctricos de la Red Metropolitana de
Movilidad. Cada bus tiene batería limitada y se recarga en electroterminales con pocos
cargadores. Queremos cubrir todos los viajes al menor costo (buses + electricidad + kilómetros
en vacío). En la literatura se llama **MD-E-VSP** (*Multi-Depot Electric Vehicle Scheduling
Problem*) con programación de recargas.

> **¿Llegas nuevo al proyecto o trabajas con otra IA?** Lee primero
> [`CONTEXTO-DEL-PROYECTO.md`](CONTEXTO-DEL-PROYECTO.md): qué se hizo en cada entrega, los resultados,
> las decisiones tomadas, lo que falta y las trampas conocidas.

## Mapa de carpetas

Las carpetas con número siguen el orden del semestre; las que no tienen número son el código
que se usa en todas las entregas.

| Carpeta | Qué hay | ¿Está en GitHub? |
|---|---|---|
| `00-enunciado/` | Enunciado P7 y lineamientos de las Entregas 1, 2 y 3. | Sí |
| `01-datos/` | Datos del curso: GTFS de RED, red vial `chile.gpkg`, mapa. **Solo lectura.** | No (pesa 1,3 GB; se comparte aparte) |
| `02-analisis-datos/` | Análisis de datos de la Entrega 1: corridas, KPIs, figuras. | Sí |
| `03-resultados/` | Salidas de `02-analisis-datos/` (figuras y tablas LaTeX). | Sí |
| `04-documentos/` | Documentos de trabajo en LaTeX y sus PDF: análisis de datos, supuestos, discusión metodológica, bibliografía. | Sí |
| `05-entrega1/` | Presentación e informe entregados en la Entrega 1. | Sí |
| `08-entrega2/` | Informe 2 en LaTeX (`informe2/`), barrido de presupuesto (`sensibilidad_presupuesto/`), presentación del grupo. | Sí |
| `09-entrega3/` | Plan de la Entrega 3, mapa de sectores (`mapa_sectores/`) y estudio de tamaños de grupo (`octetos/`). | Sí |
| `codigo/` | Código base del grupo: Fase 1 (`fase1/`), prototipo de tres fases y **caso base miope** (`tres_fases/caso_base.py`). | Sí; de `output/` solo los resúmenes |
| `metodo_hibrido/` | **Método principal**: construcción cronológica + mejora por pares, tríos y cuartetos con Gurobi, y su verificador. | Sí; de `resultados/` solo los resúmenes, sin instancias |
| `caso_base_simple_gurobi/` | Caso base sin recargas resuelto con Gurobi (comparación de la Entrega 2). | Sí; de la corrida solo el resumen y las jornadas |

No se suben: entornos de Python (`.venv*`), licencias de Gurobi, instancias y corridas
pesadas. Las reglas están en [`.gitignore`](.gitignore).

## Dónde están los resultados

De cada corrida se suben los resúmenes; los planes completos (`planes.json`, `actividades.csv`,
20-50 MB cada uno) se regeneran con los scripts.

| Resultado | Archivos |
|---|---|
| Método híbrido, red completa L / S / D | `metodo_hibrido/resultados/completa_417_20261006/`, `completa_417_S_20261027/`, `completa_417_D_20261027/`: `INFORME.md` (solo L), `comparacion_etapas.csv`, `comparacion.json`, `verificacion_final.json`, `04_final/resumen.json`, `04_final/jornadas.csv` (un bus por fila), `04_final/recargas.csv` |
| Resumen escrito del método híbrido | `metodo_hibrido/RESULTADOS.md` |
| Barrido de presupuesto (Entrega 2) | `metodo_hibrido/resultados/presupuesto/B*_r*/` y `08-entrega2/sensibilidad_presupuesto/resumen_barrido.csv` |
| Caso base miope L / S / D | `codigo/output/tres_fases/red_417_*_caso_base/`: `resumen.json`, `jornadas.csv`, `recargas.csv` |
| Caso base simple con Gurobi | `caso_base_simple_gurobi/corrida_gurobi/resumen.json`, `jornadas.csv` |
| Tamaños de grupo y distancia al óptimo (Entrega 3) | `09-entrega3/octetos/resultados/*.csv` y `09-entrega3/octetos/distancia_optimo/distancia_optimo.pdf` |
| Análisis de datos (Entrega 1) | `03-resultados/` |
| Cifras del informe 2 | `08-entrega2/informe2/salidas/` |

## Preparar el computador (una vez)

Desde la raíz del repositorio:

```bash
python3 -m venv .venv-optimizacion
```

```bash
.venv-optimizacion/bin/pip install "gurobipy>=12,<13" numpy scipy pandas matplotlib pytest
```

La licencia gratuita de `gurobipy` sirve para casos chicos. Para los grandes hace falta la
licencia académica (`grbgetkey ...`).

## Cómo correr lo principal

**Estudio de tamaños de grupo (Entrega 3).** Compara pares, tríos y cuartetos contra la
solución exacta. Las instrucciones paso a paso para correr la exacta en los casos medianos están
en [`09-entrega3/octetos/INSTRUCCIONES-EXACTA-MEDIANOS.md`](09-entrega3/octetos/INSTRUCCIONES-EXACTA-MEDIANOS.md).

```bash
bash 09-entrega3/octetos/correr_todo.sh
```

**Método híbrido** sobre la red completa o una muestra: ver [`metodo_hibrido/README.md`](metodo_hibrido/README.md).

```bash
.venv-optimizacion/bin/python metodo_hibrido/ejecutar.py
```

**Caso base miope** (cada ruta con sus propios buses): ver [`codigo/tres_fases/CASO_BASE.md`](codigo/tres_fases/CASO_BASE.md).

**Informe 2** (las cifras salen de los scripts, no se escriben a mano):

```bash
cd 08-entrega2/informe2 && ./compilar.sh
```

**Análisis de datos de la Entrega 1** (escribe en `03-resultados/`):

```bash
.venv-optimizacion/bin/python 02-analisis-datos/analisis_datos.py
```

## Pruebas

Cada carpeta de código trae sus pruebas (`test_*.py`). Para correrlas todas, carpeta por
carpeta:

```bash
for d in codigo/fase1 codigo/tres_fases metodo_hibrido caso_base_simple_gurobi 08-entrega2/informe2/scripts 08-entrega2/sensibilidad_presupuesto 09-entrega3/octetos 09-entrega3/scripts 09-entrega3/mapa_sectores; do .venv-optimizacion/bin/python -m pytest -q "$d"; done
```

Algunas pruebas necesitan `01-datos/` o corridas guardadas que no están en GitHub.

## Supuestos principales

| Supuesto | Valor | Dónde |
|---|---|---|
| Día analizado | Laboral (`L`); también sábado (`S`) y domingo (`D`) en la Entrega 3 | `02-analisis-datos/analisis_datos.py`, `metodo_hibrido/` |
| Solo buses (se descartan Metro y Metrotren) | `route_type == 3` | `02-analisis-datos/analisis_datos.py` |
| Batería al 100 % al empezar el día | sin reinicio diario | `codigo/tres_fases/README.md` |
| Electroterminales | los 5 del enunciado | `codigo/depots.csv`, `codigo/charger_capacity.csv` |

## Historia

- El 11-nov-2026 se ordenó el repositorio: `CODIGO apstone/` pasó a llamarse `codigo/` (el código
  acepta los dos nombres) y `02-codigo/` pasó a `02-analisis-datos/`. Los documentos de planificación
  antiguos (`PLAN*.md`, `ESQUEMA.md`) conservan los nombres viejos.
- Se quitaron la guía de la interrogación 1, la plantilla de ejemplo del informe y los binarios de
  Windows (`.deps`), que hacían fallar las pruebas en Mac.
