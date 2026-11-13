#!/usr/bin/env bash
# Revisa solo lineas nuevas del log y registra alertas. No repite alertas viejas.
set -uo pipefail
cd "$(dirname "$0")"
LOG=autopush.log
STATE=.alert_state
ALERT=alertas.log
mkdir -p status

TOTAL=0
NUEVAS=0
ALERTAS=0
ESTADO=DONE
[ -f "$LOG" ] && TOTAL=$(wc -l < "$LOG" | tr -d ' ')
LAST=$(cat "$STATE" 2>/dev/null || echo 0)
case "$LAST" in (*[!0-9]*|'') LAST=0 ;; esac

if [ "$TOTAL" -gt "$LAST" ]; then
  NUEVAS=$((TOTAL - LAST))
  NUEVO=$(tail -n +$((LAST + 1)) "$LOG")
  echo "$TOTAL" > "$STATE"
  if echo "$NUEVO" | grep -qiE "error|rejected|GH013|fatal"; then
    ALERTAS=1
    { echo "=== $(date '+%F %T') ==="; echo "$NUEVO"; } >> "$ALERT"
    if command -v mail >/dev/null 2>&1; then
      echo "$NUEVO" | mail -s "[MGP-Prospeccion] Error de push" pereba.group@gmail.com || true
    fi
  fi
fi

NOW=$(date '+%Y-%m-%d %H:%M:%S')
printf '{"state":"%s","lineas_nuevas":%s,"alertas":%s,"log_total":%s,"updated":"%s"}\n' \
  "$ESTADO" "$NUEVAS" "$ALERTAS" "$TOTAL" "$NOW" > status/alert_bot.json
