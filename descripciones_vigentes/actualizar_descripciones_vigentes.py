#!/usr/bin/env python3
"""
actualizar_descripciones_vigentes.py
Genera y actualiza los textos copiables sin emojis para las propiedades vigentes (activas a republicar).
Consume directamente el catálogo maestro de organizador_propiedades_autonomo.py para garantizar
que todas las propiedades activas tengan sus 3 variantes sin emojis disponibles para copiar con 1 clic.
"""

import json
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, 'descripciones_vigentes')

sys.path.insert(0, BASE_DIR)
from organizador_propiedades_autonomo import CATALOGO_PROPIEDADES, clean_no_emojis

def build_descriptions():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 1. JSON
    json_path = os.path.join(OUTPUT_DIR, 'descripciones_vigentes.json')
    data_export = {
        'total_propiedades_vigentes': len(CATALOGO_PROPIEDADES),
        'propiedades': []
    }
    
    for prop in CATALOGO_PROPIEDADES:
        data_export['propiedades'].append({
            'id': prop['id'],
            'nombre': prop['nombre_oficial'],
            'operacion': prop['operacion'],
            'tipo_inmueble': prop['tipo_inmueble'],
            'precio': prop['precio_formato'],
            'ubicacion': prop['ubicacion'],
            'superficie': prop['superficie'],
            'descripciones': list(prop['descripciones'].values())
        })
        
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data_export, f, ensure_ascii=False, indent=2)
    print(f"JSON vigentes guardado: {json_path}")
    
    # 2. Markdown
    md_path = os.path.join(OUTPUT_DIR, 'descripciones_propiedades_vigentes.md')
    md = []
    md.append('# Banco de Descripciones Copiables para Propiedades Vigentes')
    md.append('> [!IMPORTANT]')
    md.append('> **REGLA ESTRICTA APLICADA:** Todos los textos están 100% libres de emojis o símbolos pictográficos para evitar filtros de spam de Facebook.')
    md.append('> Cada propiedad cuenta con **3 variantes distintas** listas para rotar en publicaciones diarias.\n')
    md.append(f'**Total de propiedades activas en inventario:** {len(CATALOGO_PROPIEDADES)}\n')
    md.append('---')
    
    for idx, prop in enumerate(CATALOGO_PROPIEDADES, 1):
        md.append(f"## {idx}. {prop['nombre_oficial']}")
        md.append(f"- **Operación:** {prop['operacion']}")
        md.append(f"- **Precio:** {prop['precio_formato']}")
        md.append(f"- **Ubicación:** {prop['ubicacion']}")
        md.append(f"- **Superficie:** {prop['superficie']}")
        md.append(f"- **Carpeta individual:** `propiedades/{prop['folder_name']}/`\n")
        
        for v_num, (v_key, v_text) in enumerate(prop['descripciones'].items(), 1):
            v_title = v_key.replace('_', ' ').title()
            md.append(f"### Variante {v_num}: {v_title}")
            md.append("```text")
            md.append(v_text)
            md.append("```\n")
            
        md.append('---\n')
        
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Markdown vigentes guardado: {md_path}")
    
    # 3. Archivo de texto plano directo para copiado (.txt)
    txt_path = os.path.join(OUTPUT_DIR, 'descripciones_propiedades_vigentes.txt')
    txt_lines = []
    txt_lines.append("=" * 80)
    txt_lines.append("BANCO DE TEXTOS COPIABLES (SIN EMOJIS) PARA PUBLICACIONES")
    txt_lines.append("=" * 80)
    txt_lines.append("\n")
    
    for idx, prop in enumerate(CATALOGO_PROPIEDADES, 1):
        txt_lines.append(f"PROPIEDAD {idx}: {prop['nombre_oficial'].upper()}")
        txt_lines.append(f"Operacion: {prop['operacion']} | Precio: {prop['precio_formato']} | Ubicacion: {prop['ubicacion']}")
        txt_lines.append("-" * 80)
        
        for v_num, (v_key, v_text) in enumerate(prop['descripciones'].items(), 1):
            txt_lines.append(f"\n[VARIANTE {v_num} - {v_key.upper()}]\n")
            txt_lines.append(v_text)
            txt_lines.append("\n" + "." * 60)
            
        txt_lines.append("\n" + "=" * 80 + "\n")
        
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(txt_lines))
    print(f"TXT plano vigentes guardado: {txt_path}")

if __name__ == '__main__':
    build_descriptions()
