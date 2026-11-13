#!/bin/bash
# Doble clic para abrir el dashboard local de MGP Prospeccion.
cd "$(dirname "$0")" || exit 1
exec python3 dashboard_server.py
