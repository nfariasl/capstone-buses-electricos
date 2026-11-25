#!/bin/bash
# Compila el informe final: cifras → figuras → LaTeX → revisor.
set -euo pipefail
PY="${PYTHON:-$(command -v python3.12 || command -v python3)}"
cd "$(dirname "$0")"
"$PY" scripts/cifras.py
"$PY" scripts/figuras.py
latexmk -pdf -interaction=nonstopmode -halt-on-error informe3.tex
"$PY" scripts/revisar.py "$@"
