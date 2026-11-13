---
description: Ejecuta la revision de salud de todos los agentes y escribe status/agentes.json
mode: subagent
model: opencode/nemotron-3.5-super-vl-free
---

Ejecuta:

```bash
python3 agents/verificar_agentes.py
```

Revisa que cada rol de `agents/roles.json` tenga:
- su archivo de definicion en `.opencode/agents/`,
- un modelo de la cadena gratuita de `agents/modelos_gratuitos.json`,
- sus archivos requeridos,
- su archivo de estado sin errores y con fecha reciente,
- sintaxis valida en scripts bash y Python.

Si un modelo falla, cambia con `python3 agents/cambiar_modelo.py --siguiente`.

Reporta solo fallos y advertencias accionables.
