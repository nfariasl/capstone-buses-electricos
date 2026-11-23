#!/bin/bash
# Corre los escenarios físicos del día laboral (batería y consumo) junto con la instancia base, con el
# mismo método, el mismo tiempo y en el mismo computador, como correr_sensibilidad.sh.
#
# Cada escenario se corre en su propio proceso con las variables de entorno que declara su
# escenario.json («sensibilidad.entorno»): metodo_hibrido/energia.py lee BATERIA_KWH, RESERVA_KWH y
# CONSUMO_KWH_KM al importarse.
#
# Antes: crear los escenarios con
#   python3 09-entrega3/sensibilidad/crear_escenarios.py --instancia metodo_hibrido/instancia_417 \
#       --destino metodo_hibrido/sensibilidad_417_L --escenarios bateria_300 bateria_250 consumo_+10 consumo_+20
# Uso, desde la raíz del proyecto (con el computador enchufado y la tapa abierta):
#   caffeinate -i -s bash 09-entrega3/sensibilidad/correr_fisicos.sh [segundos]
set -u
cd "$(dirname "$0")/../.."
PY=.venv-optimizacion/bin/python
CORRER=09-entrega3/octetos/correr_metodos.py
ESC=metodo_hibrido/sensibilidad_417_L
RES=09-entrega3/sensibilidad/resultados
SEGUNDOS=${1:-1200}
mkdir -p "$RES"

correr() {  # correr <fila> <instancia>
    local n=$1 inst=$2 csv="$RES/fisicos_$1.csv" seguir="" entorno
    [ -f "$csv" ] && seguir="--continuar"
    entorno=$("$PY" -c 'import json, sys
s = json.load(open(sys.argv[1] + "/escenario.json", encoding="utf-8-sig"))
print(" ".join(f"{k}={v}" for k, v in s.get("sensibilidad", {}).get("entorno", {}).items()))' "$inst")
    echo "=== $(date '+%F %T') fila $n inicio: $inst [$entorno]"
    env $entorno "$PY" "$CORRER" --instancias "$inst" --metodos solo_base cuartetos --selecciones azar \
        --semillas 1 --presupuestos "$SEGUNDOS" --planes "$RES/planes_fisicos" --salida "$csv" $seguir
    echo "=== $(date '+%F %T') fila $n fin: $inst (código $?)"
}

(correr 1 metodo_hibrido/instancia_417; correr 1 "$ESC/consumo_+20") &
correr 2 "$ESC/bateria_300" &
correr 3 "$ESC/bateria_250" &
correr 4 "$ESC/consumo_+10" &
wait

"$PY" - "$RES" <<'EOF'
import csv, sys
from pathlib import Path
res = Path(sys.argv[1])
filas = [r for p in sorted(res.glob('fisicos_[0-9].csv')) for r in csv.DictReader(p.open(encoding='utf-8-sig'))]
with (res / 'fisicos_417_L.csv').open('w', encoding='utf-8-sig', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(filas[0]))
    w.writeheader()
    w.writerows(filas)
print(f'{len(filas)} filas en {res / "fisicos_417_L.csv"}')
EOF
echo "=== $(date '+%F %T') fin de los escenarios físicos"
