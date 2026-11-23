#!/bin/bash
# Corre el caso base (codigo/tres_fases/caso_base.py) con la batería y el consumo de cada escenario
# físico, para medir el ahorro contra el caso base de la misma batería o el mismo consumo.
# Toma las variables de entorno de «sensibilidad.entorno» en el escenario.json de cada escenario, igual
# que correr_fisicos.sh. Cada corrida toma ~5 s. Después: python3 ahorro_fisicos.py
# Uso, desde la raíz del proyecto: bash 09-entrega3/sensibilidad/caso_base_fisicos.sh
set -eu
cd "$(dirname "$0")/../.."
PY=.venv-optimizacion/bin/python
ESC=metodo_hibrido/sensibilidad_417_L
OUT=codigo/output/tres_fases/sensibilidad_fisicos
mkdir -p "$OUT"
for e in bateria_300 bateria_250 consumo_+10 consumo_+20; do
    entorno=$("$PY" -c 'import json, sys
s = json.load(open(sys.argv[1] + "/escenario.json", encoding="utf-8-sig"))
print(" ".join(f"{k}={v}" for k, v in s["sensibilidad"]["entorno"].items()))' "$ESC/$e")
    echo "=== $e [$entorno]"
    (cd codigo && env $entorno "../$PY" tres_fases/caso_base.py --instancia ../metodo_hibrido/instancia_417 \
        --salida "output/tres_fases/sensibilidad_fisicos/$e" > /dev/null)
done
