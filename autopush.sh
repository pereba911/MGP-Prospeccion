#!/usr/bin/env bash
set -euo pipefail
cd /home/poster/mgp-prospeccion
if [ -f .env ]; then set -a; . ./.env; set +a; fi
: "${GITHUB_TOKEN:?GITHUB_TOKEN no configurado en .env}"
AUTH="http.extraHeader=Authorization: token ${GITHUB_TOKEN}"
git add -A
git commit -m "Automated update $(date +'%Y-%m-%d %H:%M:%S')" || true
git -c "$AUTH" pull --rebase --autostash origin main || true
git -c "$AUTH" push origin main
