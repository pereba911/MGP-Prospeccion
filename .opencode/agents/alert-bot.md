---
description: Revisa lineas nuevas del log y registra alertas de error
mode: subagent
model: opencode/beam-free
---

Responsable de `alert_bot.sh`.

Reglas:
- Procesa solo lineas nuevas desde `.alert_state`; no repitas alertas viejas.
- Detecta `error`, `rejected`, `GH013` y `fatal`.
- Guarda la alerta en `alertas.log`.
- Envia la alerta por WhatsApp con `agents/notificar_whatsapp.py` (proveedor en `.env`).
- Si faltan credenciales, no falles: el estado queda como `sin_configurar`.
- Escribe `status/alert_bot.json` con `state`, `lineas_nuevas`, `alertas`, `whatsapp` y `updated`.

No borres los logs.
