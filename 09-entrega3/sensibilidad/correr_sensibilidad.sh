#!/bin/bash
# Corre los escenarios de sensibilidad del día laboral junto con la instancia base, con el mismo método,
# el mismo tiempo y en el mismo computador, para que el Δ % de cada escenario contra la base sea justo.
#
# Método: plan inicial (solo_base) y cuartetos al azar, semilla 1 (el método elegido en la Entrega 3).
# Cuatro filas en paralelo, una por núcleo de rendimiento del M1; cada fila escribe su propia tabla y al
# final se juntan en sensibilidad_417_L.csv. Si se corta, basta volver a ejecutarlo (--continuar).
#
# Antes: crear los escenarios con crear_escenarios.py (ver README.md).
# Uso, desde la raíz del proyecto (con el computador enchufado y la tapa abierta):
#   caffeinate -i -s bash 09-entrega3/sensibilidad/correr_sensibilidad.sh [segundos]
set -u
cd "$(dirname "$0")/../.."
PY=.venv-optimizacion/bin/python
CORRER=09-entrega3/octetos/correr_metodos.py
ESC=metodo_hibrido/sensibilidad_417_L
RES=09-entrega3/sensibilidad/resultados
SEGUNDOS=${1:-1200}
mkdir -p "$RES"

fila() {  # fila <número> <instancias...>
    local n=$1; shift
    local csv="$RES/fila_$n.csv" seguir=""
    [ -f "$csv" ] && seguir="--continuar"
    echo "=== $(date '+%F %T') fila $n inicio: $*"
    "$PY" "$CORRER" --instancias "$@" --metodos solo_base cuartetos --selecciones azar --semillas 1 \
        --presupuestos "$SEGUNDOS" --planes "$RES/planes" --salida "$csv" $seguir
    echo "=== $(date '+%F %T') fila $n fin (código $?)"
}

fila 1 metodo_hibrido/instancia_417 $ESC/cierre_E1 $ESC/cierre_E5 &
fila 2 $ESC/plazas_-20 $ESC/plazas_+20 $ESC/plazas_+50 &
fila 3 $ESC/conexiones_-50 $ESC/cierre_E2 $ESC/tarifa_punta_+50 &
fila 4 $ESC/cierre_E3 $ESC/cierre_E4 $ESC/plazas_por_demanda &
wait

"$PY" - "$RES" <<'EOF'
import csv, sys
from pathlib import Path
res = Path(sys.argv[1])
filas = [r for p in sorted(res.glob('fila_*.csv')) for r in csv.DictReader(p.open(encoding='utf-8-sig'))]
with (res / 'sensibilidad_417_L.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0]))
    w.writeheader()
    w.writerows(filas)
print(f'{len(filas)} filas en {res / "sensibilidad_417_L.csv"}')
EOF
echo "=== $(date '+%F %T') fin de la sensibilidad"
