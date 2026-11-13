#!/usr/bin/env bash
cd /home/poster/mgp-prospeccion
LOG=autopush.log
STATE=.alert_state
ALERT=alertas.log
[ -f "$LOG" ] || exit 0
TOTAL=$(wc -l < "$LOG" | tr -d ' ')
LAST=$(cat "$STATE" 2>/dev/null || echo 0)
[ "$TOTAL" -gt "$LAST" ] || exit 0
NUEVO=$(tail -n +$((LAST+1)) "$LOG")
echo "$TOTAL" > "$STATE"
if echo "$NUEVO" | grep -qiE "error|rejected|GH013|fatal"; then
  { echo "=== $(date '+%F %T') ==="; echo "$NUEVO"; } >> "$ALERT"
  if command -v mail >/dev/null 2>&1; then
    echo "$NUEVO" | mail -s "[MGP-Prospeccion] Error de push" pereba.group@gmail.com || true
  fi
fi
