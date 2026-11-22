#!/bin/bash
# Cola nocturna del 22-nov: (1) casos con recarga forzada (batería de 150 y 120 kWh) y (2) la respuesta
# perfecta en casos más grandes (hasta 12 rutas y 442 corridas), lo que pidieron el profesor y Gustavo.
#
# La respuesta perfecta usa el modelo podado (exacta_podada en correr_metodos.py): mismo óptimo, pero cabe
# en 8 GB. Si no termina en el tiempo dado, la tabla igual anota la cota inferior de Gurobi (cota_usd).
# Va de lo más importante a lo menos; si se corta, basta volver a ejecutarlo (cada etapa usa --continuar).
#
# Uso, desde la raíz del proyecto (con el computador enchufado y la tapa abierta):
#   caffeinate -i -s bash 09-entrega3/octetos/correr_noche.sh >> 09-entrega3/octetos/resultados/noche.log 2>&1
set -u
cd "$(dirname "$0")/../.."
PY=.venv-optimizacion/bin/python
CORRER=09-entrega3/octetos/correr_metodos.py
RES=09-entrega3/octetos/resultados
CASOS=09-entrega3/octetos/casos
HEURISTICAS="solo_base pares_trios cuartetos"
HILOS_EXACTA=4
mkdir -p "$RES"

etapa() {  # etapa <nombre> <batería kWh> <csv> <argumentos...>
    local nombre=$1 bateria=$2 csv=$3; shift 3
    local seguir=""
    [ -f "$csv" ] && seguir="--continuar"
    echo "=== $(date '+%F %T') inicio: $nombre (batería $bateria kWh)"
    BATERIA_KWH=$bateria "$PY" "$CORRER" "$@" --salida "$csv" $seguir
    echo "=== $(date '+%F %T') fin: $nombre (código $?)"
}
exacta() {  # exacta <nombre> <batería> <csv> <segundos> <casos...>
    local nombre=$1 bateria=$2 csv=$3 segundos=$4; shift 4
    etapa "$nombre" "$bateria" "$csv" --instancias "$@" --metodos exacta_podada \
        --presupuestos "$segundos" --presupuesto-exacta "$segundos" --hilos-exacta $HILOS_EXACTA
}
heuristicas() {  # heuristicas <nombre> <batería> <csv> <segundos> <casos...>
    local nombre=$1 bateria=$2 csv=$3 segundos=$4; shift 4
    etapa "$nombre" "$bateria" "$csv" --instancias "$@" --metodos $HEURISTICAS \
        --selecciones azar --semillas 1 --presupuestos "$segundos"
}

# 1. Recarga forzada, 150 kWh: ¿la respuesta perfecta ahora recarga? (15 min por caso)
exacta "recarga 150 exacta" 150 "$RES/recarga_bat150_exacta.csv" 900 $CASOS/bat150_*
# 2. Diez rutas (293 corridas) y el mediano de 200, con la respuesta perfecta.
exacta "10 rutas exacta" 350 "$RES/casos_rutas_exacta.csv" 3600 $CASOS/rutas_10_sector_2
exacta "mediano 200 exacta" 350 "$RES/casos_medianos_exacta_podada.csv" 2400 $CASOS/mediano_200_sector_1_2_rutas
# 3. Heurísticas en esos mismos casos, para medir la distancia a la respuesta perfecta.
heuristicas "recarga 150 heurísticas" 150 "$RES/recarga_bat150.csv" 120 $CASOS/bat150_*
heuristicas "10 rutas heurísticas" 350 "$RES/casos_rutas.csv" 300 $CASOS/rutas_10_sector_2
heuristicas "mediano 200 heurísticas" 350 "$RES/casos_medianos.csv" 300 $CASOS/mediano_200_sector_1_2_rutas
# 4. Recarga forzada, 120 kWh (100 kWh no alcanza para algunos servicios por sí solos).
exacta "recarga 120 exacta" 120 "$RES/recarga_bat120_exacta.csv" 900 $CASOS/bat120_*
heuristicas "recarga 120 heurísticas" 120 "$RES/recarga_bat120.csv" 120 $CASOS/bat120_*
# 5. El resto de las escaleras, si queda noche.
exacta "rutas 6, 8 y 12 exacta" 350 "$RES/casos_rutas_exacta.csv" 3600 \
    $CASOS/rutas_06_sector_2 $CASOS/rutas_08_sector_2 $CASOS/rutas_12_sector_2
heuristicas "rutas 6, 8 y 12 heurísticas" 350 "$RES/casos_rutas.csv" 300 \
    $CASOS/rutas_06_sector_2 $CASOS/rutas_08_sector_2 $CASOS/rutas_12_sector_2
exacta "medianos 250 a 400 exacta" 350 "$RES/casos_medianos_exacta_podada.csv" 3600 \
    $CASOS/mediano_250_sector_1_3_rutas $CASOS/mediano_300_sector_1_4_rutas $CASOS/mediano_400_sector_1_5_rutas
heuristicas "medianos 250 a 400 heurísticas" 350 "$RES/casos_medianos.csv" 300 \
    $CASOS/mediano_250_sector_1_3_rutas $CASOS/mediano_300_sector_1_4_rutas $CASOS/mediano_400_sector_1_5_rutas
echo "=== $(date '+%F %T') noche terminada"
