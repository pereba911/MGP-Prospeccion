#!/usr/bin/env bash
# Wrapper del pipeline de fotos (iluminación + cap 7020 px) usando Pillow.
# No requiere ImageMagick ni agentes/LLM.
set -euo pipefail
cd "$(dirname "$0")"
exec python3 procesar_fotos.py --todo "$@"
