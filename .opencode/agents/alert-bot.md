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
- Si existe `mail`, envia correo; si no existe, no falles.
- Escribe `status/alert_bot.json` con `state`, `lineas_nuevas`, `alertas` y `updated`.

No borres los logs.
