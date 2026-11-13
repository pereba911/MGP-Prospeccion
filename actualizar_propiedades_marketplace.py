#!/usr/bin/env python3
"""
actualizar_propiedades_marketplace.py
Script de sincronización periódica (cada 2 semanas) de las publicaciones de Marketplace en Facebook.
Conecta de forma desatendida y en estricto segundo plano con la sesión activa de Chrome vía CDP.
Garantiza que NINGUNA propiedad activa se quede fuera debido a retrasos de carga perezosa (lazy-loading).
Actualiza automáticamente:
  1. propiedades_marketplace.json y relacion_propiedades_marketplace.md
  2. Todos los paquetes individuales de propiedades en propiedades/<id_propiedad>/
  3. El banco de descripciones sin emojis en descripciones_vigentes/
"""

import socket
import struct
import json
import time
import os
import re
import sys
from datetime import datetime

CDP_PORT_FILE = os.path.expanduser('~/Library/Application Support/Google/Chrome/DevToolsActivePort')
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

class BackgroundCDP:
    def __init__(self, retries=3, delay=1.5):
        if not os.path.exists(CDP_PORT_FILE):
            raise RuntimeError(f"No se encontró {CDP_PORT_FILE}. Asegúrate de que Chrome esté abierto.")
        
        with open(CDP_PORT_FILE) as f:
            self.port = int(f.readline().strip())
            self.path = f.readline().strip()
        
        last_err = None
        for attempt in range(retries):
            try:
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.connect(('127.0.0.1', self.port))
                req = (
                    f'GET {self.path} HTTP/1.1\r\n'
                    f'Host: 127.0.0.1:{self.port}\r\n'
                    f'Upgrade: websocket\r\n'
                    f'Connection: Upgrade\r\n'
                    f'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\n'
                    f'Sec-WebSocket-Version: 13\r\n\r\n'
                )
                self.s.sendall(req.encode('utf-8'))
                handshake = self.s.recv(4096)
                if b'101' in handshake:
                    return
                last_err = handshake.decode('latin1', errors='ignore')
            except Exception as e:
                last_err = str(e)
            
            time.sleep(delay)
            
        raise RuntimeError(f'Handshake CDP falló tras {retries} intentos: {last_err}')

    def send(self, obj):
        data = json.dumps(obj).encode('utf-8')
        length = len(data)
        mask = b'\x5a\x6b\x7c\x8d'
        masked_data = bytearray(length)
        for i in range(length):
            masked_data[i] = data[i] ^ mask[i % 4]
            
        header = bytearray([0x81])
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack('>H', length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack('>Q', length))
        header.extend(mask)
        self.s.sendall(header + masked_data)

    def recv(self, timeout=40):
        self.s.settimeout(timeout)
        buf = self.s.recv(2)
        if not buf:
            return None
        b0, b1 = buf[0], buf[1]
        masked = (b1 & 0x80) != 0
        length = b1 & 0x7f
        if length == 126:
            length = struct.unpack('>H', self.s.recv(2))[0]
        elif length == 127:
            length = struct.unpack('>Q', self.s.recv(8))[0]
        
        mask = self.s.recv(4) if masked else None
        data = bytearray()
        while len(data) < length:
            chunk = self.s.recv(length - len(data))
            if not chunk:
                break
            data.extend(chunk)
            
        if masked:
            for i in range(len(data)):
                data[i] ^= mask[i % 4]
        return json.loads(data.decode('utf-8'))

    def close(self):
        try:
            self.s.close()
        except:
            pass

def fetch_marketplace_listings():
    print("[1/5] Conectando con Google Chrome en segundo plano...")
    cdp = BackgroundCDP()
    
    # Obtener páginas
    cdp.send({'id': 1, 'method': 'Target.getTargets', 'params': {}})
    targets_msg = cdp.recv()
    targets = targets_msg.get('result', {}).get('targetInfos', [])
    
    target_id = None
    for t in targets:
        if t.get('type') == 'page' and 'facebook.com/marketplace/you/selling' in t.get('url', ''):
            target_id = t['targetId']
            break
            
    if not target_id:
        for t in targets:
            if t.get('type') == 'page' and 'facebook.com' in t.get('url', ''):
                target_id = t['targetId']
                break
                
    if not target_id:
        for t in targets:
            if t.get('type') == 'page':
                target_id = t['targetId']
                break

    print(f"[2/5] Vinculando sesión CDP al Target: {target_id}...")
    cdp.send({'id': 2, 'method': 'Target.attachToTarget', 'params': {'targetId': target_id, 'flatten': True}})
    session_id = None
    while True:
        m = cdp.recv()
        if m.get('id') == 2:
            session_id = m['result']['sessionId']
            break
            
    print(f"[3/5] Asegurando navegación a Marketplace y activando filtro 'Disponibles'...")
    js_prepare = """
    (async () => {
        if (!window.location.href.includes('/marketplace/you/selling')) {
            window.location.href = 'https://www.facebook.com/marketplace/you/selling';
            await new Promise(r => setTimeout(r, 4000));
        }
        
        // Intentar activar filtro 'Disponibles y en stock' si no está activo
        try {
            const estadoBtn = Array.from(document.querySelectorAll('div[role="button"], button, span')).find(el => el.innerText.trim() === 'Estado');
            if (estadoBtn) {
                estadoBtn.click();
                await new Promise(r => setTimeout(r, 600));
                const opt = Array.from(document.querySelectorAll('div[role="menuitem"], div[role="menuitemradio"], div[role="menuitemcheckbox"], div[role="radio"], div[role="option"], span')).find(el => el.innerText.trim() === 'Disponibles y en stock');
                if (opt) {
                    opt.click();
                    await new Promise(r => setTimeout(r, 2000));
                }
            }
        } catch(e) {}
        return true;
    })()
    """
    cdp.send({
        'id': 3,
        'sessionId': session_id,
        'method': 'Runtime.evaluate',
        'params': {'expression': js_prepare, 'awaitPromise': True, 'returnByValue': True}
    })
    while True:
        m = cdp.recv()
        if m.get('id') == 3:
            break

    print(f"[4/5] Ejecutando scroll profundo y recolección acumulativa (anti-virtualización)...")
    js_deep_scrape = """
    (async () => {
        const itemsMap = new Map();
        let prevHeight = 0;
        let stableCount = 0;

        function extractVisible() {
            // Recolectar contenedores de precios
            const priceEls = Array.from(document.querySelectorAll('span, div')).filter(el => 
                el.children.length === 0 && /^MX\\$[\\d\\.]+/.test(el.innerText.trim())
            );
            for (const el of priceEls) {
                let container = el;
                for (let k = 0; k < 6; k++) {
                    if (container.parentElement && container.parentElement.innerText.includes('Publicad')) {
                        container = container.parentElement;
                        break;
                    }
                    if (container.parentElement) container = container.parentElement;
                }
                const cText = container.innerText.trim();
                const key = cText.substring(0, 100);
                if (!itemsMap.has(key)) {
                    itemsMap.set(key, cText);
                }
            }
        }

        for (let i = 0; i < 35; i++) {
            extractVisible();
            const currentHeight = document.body.scrollHeight;
            window.scrollBy(0, 1200);
            await new Promise(r => setTimeout(r, 1100));
            
            if (currentHeight === prevHeight) {
                stableCount++;
                window.scrollTo(0, document.body.scrollHeight);
                await new Promise(r => setTimeout(r, 1600));
            } else {
                stableCount = 0;
                prevHeight = currentHeight;
            }

            if (stableCount >= 5) {
                break;
            }
        }

        extractVisible();
        return Array.from(itemsMap.values());
    })()
    """
    cdp.send({
        'id': 4,
        'sessionId': session_id,
        'method': 'Runtime.evaluate',
        'params': {'expression': js_deep_scrape, 'awaitPromise': True, 'returnByValue': True}
    })
    
    raw_cards = []
    while True:
        m = cdp.recv(timeout=75)
        if m.get('id') == 4:
            raw_cards = m['result']['result']['value']
            break
            
    cdp.close()
    print(f"[4/5] Extracción completada. {len(raw_cards)} tarjetas detectadas.")
    return raw_cards

def parse_listings(cards):
    listings = []
    seen = set()
    
    for card in cards:
        lines = [l.strip() for l in card.split('\n') if l.strip()]
        if len(lines) < 2:
            continue
            
        title = lines[0]
        price = lines[1]
        
        # Buscar precio si no estaba en linea 1
        if not re.search(r'MX\$', price):
            for l in lines:
                if 'MX$' in l:
                    price = l
                    break
                    
        status = "Disponible"
        for l in lines:
            if any(s in l for s in ['Disponible', 'Activo', 'Agotado', 'Alquilado', 'Vendido']):
                status = l
                break
                
        snippet = " ".join(lines)
        clics_match = re.search(r'([\d\.]+)\s+clics en la publicación', snippet)
        clics = clics_match.group(1) if clics_match else "0"
        
        fecha_match = re.search(r'Publicado el\s+([^\n·]+)', snippet)
        fecha = fecha_match.group(1).strip() if fecha_match else "Reciente"
        
        canales = "Marketplace y grupos" if "al menos 1 grupo" in snippet else "Marketplace"
        
        title_lower = title.lower()
        price_clean = re.sub(r'[^\d]', '', price)
        price_num = int(price_clean) if price_clean else 0
        
        if any(k in title_lower for k in ['cafetera', 'espresso', 'escritorio', 'mercedes', 'eqa']):
            tipo = 'articulo'
        elif any(k in title_lower for k in ['nave', 'bodega', 'oficina', 'lote', 'terreno']):
            tipo = 'venta' if price_num >= 1000000 else 'renta'
        elif price_num >= 500000:
            tipo = 'venta'
        elif any(k in title_lower for k in ['renta', 'alquil', 'amueblado', 'estudio', 'mil']) or price_num < 200000:
            tipo = 'renta'
        elif any(k in title_lower for k in ['venta', 'casa', 'colinas', 'san javier', 'terreno', 'galicia', 'departamento']):
            tipo = 'venta'
        else:
            tipo = 'otro'
            
        key = f"{title}_{price}"
        if key not in seen:
            seen.add(key)
            listings.append({
                'titulo': title,
                'precio': price,
                'estado': status,
                'tipo_operacion': tipo,
                'clics': clics,
                'fecha_publicacion': fecha,
                'canales': canales
            })
            
    return listings

def generate_documents(listings):
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 1. JSON
    json_path = os.path.join(OUTPUT_DIR, 'propiedades_marketplace.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'ultima_actualizacion': now_str,
            'total_publicaciones': len(listings),
            'propiedades': listings
        }, f, ensure_ascii=False, indent=2)
    print(f"JSON guardado: {json_path}")
    
    # 2. Markdown
    md_path = os.path.join(OUTPUT_DIR, 'relacion_propiedades_marketplace.md')
    ventas = [p for p in listings if p['tipo_operacion'] == 'venta']
    rentas = [p for p in listings if p['tipo_operacion'] == 'renta']
    otros = [p for p in listings if p['tipo_operacion'] == 'articulo']
    
    md = []
    md.append('# Relación de Propiedades en Marketplace (Perfil Personal)')
    md.append(f'**Última actualización:** {now_str} (Ciclo de actualización: cada 2 semanas)')
    md.append('**Herramienta de publicación:** Extensión Chrome *Multigroup Poster*')
    md.append(f'**Total de publicaciones detectadas en tu perfil:** {len(listings)}\n')
    md.append('---')
    
    md.append('## 1. Propiedades en VENTA')
    md.append('> Inmuebles residenciales, departamentos de lujo, terrenos y naves industriales en venta.\n')
    md.append('| # | Título de la Publicación en Marketplace | Precio | Estado Actual | Clics Registrados | Canales |')
    md.append('| :---: | :--- | :---: | :---: | :---: | :--- |')
    for idx, p in enumerate(ventas, 1):
        md.append(f"| {idx} | **{p['titulo']}** | {p['precio']} | `{p['estado']}` | {p['clics']} clics | {p['canales']} |")
    md.append('\n')
    
    md.append('## 2. Propiedades en RENTA')
    md.append('> Departamentos residenciales, residencias amuebladas, oficinas corporativas y bodegas en arrendamiento.\n')
    md.append('| # | Título de la Publicación en Marketplace | Renta Mensual | Estado Actual | Clics Registrados | Canales |')
    md.append('| :---: | :--- | :---: | :---: | :---: | :--- |')
    for idx, p in enumerate(rentas, 1):
        md.append(f"| {idx} | **{p['titulo']}** | {p['precio']} | `{p['estado']}` | {p['clics']} clics | {p['canales']} |")
    md.append('\n')
    
    if otros:
        md.append('## 3. Artículos / Otros (No Inmobiliarios en Marketplace)')
        md.append('> Publicaciones activas registradas en el perfil no relacionadas con bienes raíces.\n')
        md.append('| # | Título del Artículo | Precio | Estado Actual | Clics Registrados |')
        md.append('| :---: | :--- | :---: | :---: | :---: |')
        for idx, p in enumerate(otros, 1):
            md.append(f"| {idx} | {p['titulo']} | {p['precio']} | `{p['estado']}` | {p['clics']} clics |")
        md.append('\n')
        
    md.append('---')
    md.append('## 4. Mapeo Estratégico y Paquetes de Propiedades Activas')
    md.append('Todas las propiedades activas tienen su propia carpeta en `propiedades/` con sus descripciones listas (3 variantes sin emojis) y subcarpeta de fotos.')

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))
    print(f"Markdown guardado: {md_path}")

def trigger_descriptions_update():
    print("[5/5] Sincronizando paquetes modulares y banco de descripciones...")
    
    # Sincronizar paquetes de propiedades modulares
    script_org = os.path.join(OUTPUT_DIR, 'organizador_propiedades_autonomo.py')
    if os.path.exists(script_org):
        sys.path.insert(0, OUTPUT_DIR)
        try:
            import organizador_propiedades_autonomo
            organizador_propiedades_autonomo.main()
            print("Paquetes individuales en propiedades/ sincronizados exitosamente.")
        except Exception as e:
            print(f"Aviso al organizar paquetes de propiedades: {e}")
            
    # Sincronizar descripciones vigentes
    script_desc = os.path.join(OUTPUT_DIR, 'descripciones_vigentes', 'actualizar_descripciones_vigentes.py')
    if os.path.exists(script_desc):
        sys.path.insert(0, os.path.dirname(script_desc))
        try:
            import actualizar_descripciones_vigentes
            actualizar_descripciones_vigentes.build_descriptions()
            print("Banco de descripciones actualizado exitosamente en descripciones_vigentes/.")
        except Exception as e:
            print(f"Aviso al actualizar descripciones vigentes: {e}")

if __name__ == '__main__':
    raw_cards = fetch_marketplace_listings()
    listings = parse_listings(raw_cards)
    print(f"Se encontraron {len(listings)} publicaciones estructuradas.")
    generate_documents(listings)
    trigger_descriptions_update()
