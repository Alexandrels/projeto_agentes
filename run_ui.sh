#!/bin/bash
# Script para iniciar a interface Streamlit
cd "$(dirname "$0")"
source .venv/bin/activate
PYTHONPATH=. streamlit run src/ui/app.py --server.port 8501 --server.address 0.0.0.0