#!/bin/bash
# Cola del 22-nov (tarde): ¿la distancia entre las heurísticas y la respuesta perfecta en los casos con
# recarga forzada era falta de tiempo? Las heurísticas tuvieron 2 minutos; la respuesta perfecta, 15.
# Nunca usa más de 2 núcleos a la vez (con 4 el Mac se calentó demasiado).
#
#   Etapa 1: cuartetos 15 min en los 10 casos con recarga (150 y 120 kWh en paralelo, 1 núcleo cada uno).
#   Etapa 2: respuesta perfecta en 10 rutas con 150 kWh (1 h, 2 núcleos): recarga en un caso grande.
#   Etapa 3: plan base y cuartetos 15 min en ese caso, luego pares-tríos 15 min en los 10 casos chicos.
#
# Las filas nuevas van a las mismas tablas (la columna presupuesto_s separa 120 de 900 segundos). Los procesos
# en paralelo escriben siempre en tablas distintas. Si se corta, basta relanzarlo: cada etapa usa --continuar.
#
# Uso, desde la raíz del proyecto:
#   nohup caffeinate -i -s bash 09-entrega3/octetos/correr_recarga_15min.sh \
#       >> 09-entrega3/octetos/resultados/recarga_15min.log 2>&1 &
set -u
cd "$(dirname "$0")/../.."
PY=.venv-optimizacion/bin/python
CORRER=09-entrega3/octetos/correr_metodos.py
RES=09-entrega3/octetos/resultados
CASOS=09-entrega3/octetos/casos
MINUTOS_15=900
HORA=3600
HILOS_EXACTA=2
RUTAS10_150=$CASOS/bat150_rutas_10_sector_2

etapa() {  # etapa <nombre> <batería kWh> <csv> <argumentos...>
    local nombre=$1 bateria=$2 csv=$3; shift 3
    local seguir="" codigo
    [ -f "$csv" ] && seguir="--continuar"
    echo "=== $(date '+%F %T') inicio: $nombre (batería $bateria kWh)"
    BATERIA_KWH=$bateria "$PY" "$CORRER" "$@" --salida "$csv" $seguir
    codigo=$?
    echo "=== $(date '+%F %T') fin: $nombre (código $codigo)"
}
heuristica() {  # heuristica <nombre> <batería> <csv> <métodos> <casos...>
    local nombre=$1 bateria=$2 csv=$3 metodos=$4; shift 4
    etapa "$nombre" "$bateria" "$csv" --instancias "$@" --metodos $metodos \
        --selecciones azar --semillas 1 --presupuestos $MINUTOS_15
}

echo "=== $(date '+%F %T') etapa 1: cuartetos 15 min"
heuristica "cuartetos 15 min, 150 kWh" 150 "$RES/recarga_bat150.csv" cuartetos $CASOS/bat150_chico_* &
heuristica "cuartetos 15 min, 120 kWh" 120 "$RES/recarga_bat120.csv" cuartetos $CASOS/bat120_chico_* &
wait

echo "=== $(date '+%F %T') etapa 2: 10 rutas con 150 kWh, respuesta perfecta"
etapa "10 rutas 150 exacta" 150 "$RES/recarga_bat150_exacta.csv" --instancias "$RUTAS10_150" \
    --metodos exacta_podada --presupuestos $HORA --presupuesto-exacta $HORA --hilos-exacta $HILOS_EXACTA

echo "=== $(date '+%F %T') etapa 3: 10 rutas heurística y pares-tríos 15 min"
{
    heuristica "10 rutas 150, base y cuartetos 15 min" 150 "$RES/recarga_bat150.csv" "solo_base cuartetos" \
        "$RUTAS10_150"
    heuristica "pares-tríos 15 min, 150 kWh" 150 "$RES/recarga_bat150.csv" pares_trios $CASOS/bat150_chico_*
} &
heuristica "pares-tríos 15 min, 120 kWh" 120 "$RES/recarga_bat120.csv" pares_trios $CASOS/bat120_chico_* &
wait
echo "=== $(date '+%F %T') cola terminada"
