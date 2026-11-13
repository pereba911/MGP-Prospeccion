#!/usr/bin/env bash
# Revisa solo lineas nuevas del log y registra alertas. No repite alertas viejas.
# Envia la alerta por WhatsApp si .env tiene credenciales configuradas.
set -uo pipefail
cd "$(dirname "$0")"
if [ -f .env ]; then set -a; . ./.env; set +a; fi
LOG=autopush.log
STATE=.alert_state
ALERT=alertas.log
mkdir -p status

TOTAL=0
NUEVAS=0
ALERTAS=0
ESTADO=DONE
WHATSAPP=no_aplica
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

    MENSAJE=$(printf '[MGP-Prospeccion] Error detectado %s\n\n%s' \
      "$(date '+%F %T')" "$(printf '%s' "$NUEVO" | tail -n 15 | cut -c1-1100)")
    RESULTADO_WA=$(python3 agents/notificar_whatsapp.py --texto "$MENSAJE" 2>/dev/null | head -n 1)
    case "$RESULTADO_WA" in
      DONE*) WHATSAPP=enviado ;;
      SIN_CONFIGURAR*) WHATSAPP=sin_configurar ;;
      *) WHATSAPP=error ;;
    esac
  fi
fi

NOW=$(date '+%Y-%m-%d %H:%M:%S')
printf '{"state":"%s","lineas_nuevas":%s,"alertas":%s,"log_total":%s,"whatsapp":"%s","updated":"%s"}\n' \
  "$ESTADO" "$NUEVAS" "$ALERTAS" "$TOTAL" "$WHATSAPP" "$NOW" > status/alert_bot.json
