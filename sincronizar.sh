#!/usr/bin/env bash
# ==============================================================================
# MGP Prospección - Script Unificado de Sincronización y Actualización
# ==============================================================================
# Este script ejecuta todo el flujo semiautomatizado en segundo plano:
#  1. Conecta con Facebook Marketplace en Chrome (CDP).
#  2. Actualiza inventario de Marketplace (Venta / Renta).
#  3. Actualiza el banco de descripciones sin emojis (3 variantes por propiedad).
#  4. Genera y mantiene los paquetes modulares en propiedades/ con su
#     ficha de enrutamiento estricto a las listas de MultiGroup Poster.
# ==============================================================================

set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_EXEC="python3"

echo "================================================================="
echo "  MGP PROSPECCIÓN INMOBILIARIA - SINCRONIZADOR DEL AGENTE"
echo "================================================================="
echo "Iniciando proceso en segundo plano..."

# 1. Verificar que Chrome esté abierto
if ! pgrep -i "Google Chrome" > /dev/null; then
    echo "Aviso: Google Chrome no parece estar en ejecución."
    echo "Por favor abre Google Chrome e inténtalo de nuevo."
    exit 1
fi

# 2. Ejecutar el script maestro de sincronización
"$PYTHON_EXEC" "$DIR/actualizar_propiedades_marketplace.py"

echo ""
echo "================================================================="
echo "  SINCRONIZACIÓN COMPLETADA CON ÉXITO"
echo "================================================================="
echo "Archivos actualizados:"
echo "  • Reporte Marketplace:      $DIR/relacion_propiedades_marketplace.md"
echo "  • Banco de Textos (Cero emojis): $DIR/descripciones_vigentes/descripciones_propiedades_vigentes.md"
echo "  • Paquetes por Propiedad:   $DIR/propiedades/"
echo "================================================================="
