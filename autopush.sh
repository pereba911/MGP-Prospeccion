#!/usr/bin/env bash
set -euo pipefail
cd /home/poster/mgp-prospeccion
if [ -f .env ]; then set -a; . ./.env; set +a; fi
: "${GITHUB_TOKEN:?GITHUB_TOKEN no configurado en .env}"
HELPER='!f() { echo "username=x-access-token"; echo "password=$GITHUB_TOKEN"; }; f'
git add -A
git commit -m "Automated update $(date +'%Y-%m-%d %H:%M:%S')" || true
git -c credential.helper="$HELPER" pull --rebase --autostash origin main || true
git -c credential.helper="$HELPER" push origin main
