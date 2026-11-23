#!/bin/bash
# Cola del 22-nov (noche): heurísticas en los casos de 6, 8 y 12 rutas (129, 200 y 442 corridas), con el
# mismo protocolo que el caso de 10 rutas (plan base, pares-tríos y cuartetos al azar semilla 1, 5 min cada
# uno). 6 y 8 rutas ya tienen el óptimo exacto en casos_rutas_exacta.csv, así que con esto la distancia al
# óptimo se mide en tres tamaños (129, 200 y 293 corridas). 12 rutas no tiene óptimo (la exacta se cortó).
#
# Espera a que termine la sensibilidad (correr_sensibilidad.sh) para no competir por los núcleos ni ensuciar
# sus tiempos. Un solo proceso, sin paralelo. Si se corta, basta relanzarlo (usa --continuar).
#
# Uso, desde la raíz del proyecto:
#   nohup caffeinate -i -s bash 09-entrega3/octetos/correr_rutas_heuristicas.sh \
#       >> 09-entrega3/octetos/resultados/rutas_heuristicas.log 2>&1 &
set -u
cd "$(dirname "$0")/../.."
PY=.venv-optimizacion/bin/python
CORRER=09-entrega3/octetos/correr_metodos.py
RES=09-entrega3/octetos/resultados
CASOS=09-entrega3/octetos/casos
CSV="$RES/casos_rutas.csv"
SEGUNDOS=300
ESPERA_S=60

while pgrep -f "correr_sensibilidad.sh" > /dev/null; do
    sleep "$ESPERA_S"
done

seguir=""
[ -f "$CSV" ] && seguir="--continuar"
echo "=== $(date '+%F %T') inicio: heurísticas en rutas 6, 8 y 12"
BATERIA_KWH=350 "$PY" "$CORRER" --instancias \
    "$CASOS/rutas_06_sector_2" "$CASOS/rutas_08_sector_2" "$CASOS/rutas_12_sector_2" \
    --metodos solo_base pares_trios cuartetos --selecciones azar --semillas 1 \
    --presupuestos "$SEGUNDOS" --salida "$CSV" $seguir
codigo=$?
echo "=== $(date '+%F %T') fin: heurísticas en rutas 6, 8 y 12 (código $codigo)"
