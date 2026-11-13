#!/usr/bin/env bash
BATCH_DIR=/home/poster/mgp-prospeccion/fotos_batch
OUT_DIR=/processed
mkdir -p 
for IMG in /*.{jpg,jpeg,png}; do
  [ -e  ] || continue
  # Mejora de iluminación
  muapi_image_edit --input  --adjust-brightness 0.15 --adjust-contrast 0.10 --output /bright_
  # Upscale a máximo 7020 px manteniendo proporción
  muapi_enhance_upscale --input /bright_ --max-dimension 7020 --output /final_
  rm /bright_
done
echo ✅ Batch procesado – resultados en 
