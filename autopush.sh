#!/usr/bin/env bash
set -uo pipefail
cd /home/poster/mgp-prospeccion
if [ -f .env ]; then set -a; . ./.env; set +a; fi
: "${GITHUB_TOKEN:?GITHUB_TOKEN no configurado en .env}"
HELPER='!f() { echo "username=x-access-token"; echo "password=$GITHUB_TOKEN"; }; f'
git add -A
git commit -m "Automated update $(date +'%Y-%m-%d %H:%M:%S')" >/dev/null 2>&1 || true
git -c credential.helper="$HELPER" pull --rebase --autostash origin main >/dev/null 2>&1 || true
if git -c credential.helper="$HELPER" push origin main; then
  PUSH_OK=true; RESULT=DONE; CODE=0
else
  PUSH_OK=false; RESULT=ERROR; CODE=1
fi
mkdir -p status
NOW=$(date '+%Y-%m-%d %H:%M:%S')
printf '{"state":"%s","cron_active":true,"last_push_ok":%s,"last_run":"%s","updated":"%s"}\n' \
  "$RESULT" "$PUSH_OK" "$NOW" "$NOW" > status/scheduler_validator.json
exit $CODE
