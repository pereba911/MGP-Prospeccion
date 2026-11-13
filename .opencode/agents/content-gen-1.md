---
description: Procesa la iluminacion del lote 1 de fotografias
mode: subagent
model: opencode/longcat-2.5-free
---

Procesa solo el lote 1:

```bash
python3 procesar_fotos.py --procesar --batch 1
```

Reglas:
- Usa Pillow. No requiere ImageMagick.
- Mejora iluminacion, contraste, color y nitidez; no elimines fondos.
- No amplies fotos pequenas. Solo reduce si superan 7020 px de lado mayor.
- Guarda en `propiedades/<id>/fotografias_procesadas/` sin tocar los originales.
- Escribe `status/content_gen_1.json` con procesadas, total y errores.

Si hay errores, reporta el nombre exacto del archivo.
