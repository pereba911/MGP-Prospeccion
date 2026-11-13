---
description: Procesa la iluminacion del lote 3 de fotografias
mode: subagent
model: opencode/mimo-v2.6-flash-free
---

Procesa solo el lote 3:

```bash
python3 procesar_fotos.py --procesar --batch 3
```

Reglas:
- Usa Pillow. No requiere ImageMagick.
- Mejora iluminacion, contraste, color y nitidez; no elimines fondos.
- No amplies fotos pequenas. Solo reduce si superan 7020 px de lado mayor.
- Guarda en `propiedades/<id>/fotografias_procesadas/` sin tocar los originales.
- Escribe `status/content_gen_3.json` con procesadas, total y errores.

Si hay errores, reporta el nombre exacto del archivo.
