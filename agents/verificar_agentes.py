#!/usr/bin/env python3
"""Verifica que todos los agentes de MGP Prospeccion esten definidos y operen.

Comprueba, por cada rol de agents/roles.json:
  - archivo de definicion en .opencode/agents/
  - modelo dentro de la cadena gratuita
  - archivos requeridos presentes
  - archivos generados (solo advertencia si aun no existen)
  - archivo de estado sin errores y con fecha reciente
  - sintaxis valida de scripts bash y Python

Escribe status/agentes.json y devuelve codigo 1 si hay errores criticos.

Uso:
    python3 agents/verificar_agentes.py
    python3 agents/verificar_agentes.py --json
    python3 agents/verificar_agentes.py --max-dias 60
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROLES_FILE = ROOT / "agents" / "roles.json"
CHAIN_FILE = ROOT / "agents" / "modelos_gratuitos.json"
AGENTS_DIR = ROOT / ".opencode" / "agents"
CONFIG = ROOT / ".opencode" / "opencode.jsonc"
STATUS_DIR = ROOT / "status"
PROPIEDADES_DIR = ROOT / "propiedades"
LISTAS_FILE = ROOT / "listas_para_multigroup_poster.json"
CONFIG_PUBLICACION = ROOT / "config_publicacion.json"
MODELO_RE = re.compile(r"^model:\s*(\S+)\s*$", re.MULTILINE)
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF\u2600-\u27BF]")


def ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def leer_json(ruta: Path, default=None):
    try:
        with ruta.open(encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return default


def escribir_json(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def modelo_agente(ruta: Path) -> str | None:
    if not ruta.exists():
        return None
    texto = ruta.read_text(encoding="utf-8")
    if not texto.startswith("---"):
        return None
    fin = texto.find("\n---", 3)
    if fin == -1:
        return None
    match = MODELO_RE.search(texto[:fin])
    return match.group(1) if match else None


def edad_dias(valor: str | None) -> float | None:
    if not valor:
        return None
    for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            fecha = datetime.strptime(str(valor)[:19], formato)
            return (datetime.now() - fecha).total_seconds() / 86400
        except ValueError:
            continue
    return None


_sintaxis_cache: dict[str, tuple[bool, str]] = {}


def revisar_sintaxis(ruta: Path) -> tuple[bool, str]:
    clave = str(ruta)
    if clave in _sintaxis_cache:
        return _sintaxis_cache[clave]
    if not ruta.exists():
        resultado = (False, "archivo ausente")
    elif ruta.suffix == ".sh":
        proc = subprocess.run(["bash", "-n", str(ruta)], capture_output=True, text=True)
        resultado = (proc.returncode == 0, (proc.stderr or "sintaxis OK").strip())
    elif ruta.suffix == ".py":
        proc = subprocess.run(
            [sys.executable, "-m", "py_compile", str(ruta)],
            capture_output=True,
            text=True,
        )
        resultado = (proc.returncode == 0, (proc.stderr or "sintaxis OK").strip())
    else:
        resultado = (True, "sin verificacion")
    _sintaxis_cache[clave] = resultado
    return resultado


def verificar_publicacion() -> dict:
    """Comprueba coherencia entre listas, fichas y textos de produccion."""
    errores = []
    advertencias = []
    listas = leer_json(LISTAS_FILE, []) or []
    nombres = {l.get("list_name") for l in listas if isinstance(l, dict)}
    if len(nombres) != 12:
        errores.append(f"listas_para_multigroup_poster.json debe tener 12 listas, tiene {len(nombres)}")

    config = leer_json(CONFIG_PUBLICACION, {}) or {}
    whatsapp = re.sub(r"\D", "", str(config.get("whatsapp_numero", "")))
    if not whatsapp:
        advertencias.append("whatsapp_numero vacio en config_publicacion.json; los comentarios usan un marcador pendiente")

    fichas = sorted(PROPIEDADES_DIR.glob("*/ficha_publicacion.json"))
    if len(fichas) != 8:
        advertencias.append(f"se esperaban 8 fichas de propiedad, hay {len(fichas)}")

    for ruta in fichas:
        ficha = leer_json(ruta, {}) or {}
        nombre = ruta.parent.name
        estrategia = ficha.get("estrategia_multigroup_poster", {})
        asignadas = list(estrategia.get("listas_asignadas_obligatorias", []))
        faltantes = [l for l in asignadas if l not in nombres]
        if faltantes:
            errores.append(f"{nombre}: listas inexistentes {faltantes}")

        operacion = str(ficha.get("operacion", "")).lower()
        tipo = str(ficha.get("tipo_inmueble", "")).lower()
        requeridas = []
        if operacion == "venta":
            requeridas.append("1. Solo Venta (Inmuebles ZMG)")
        if operacion == "renta":
            requeridas += ["11. Solo Renta (Departamentos y Casas)", "2. Venta y Renta (Inmuebles ZMG)"]
        if tipo == "oficina":
            requeridas.append("4. Oficinas y Corporativos")
        if tipo == "terreno":
            requeridas.append("3. Terrenos y Lotes (Jalisco / ZMG)")
        if tipo in {"bodega", "nave industrial"}:
            requeridas.append("5. Bodegas y Naves Industriales")
        requeridas.append("12. Inmobiliarios Generales y Asesores ZMG")
        for lista in requeridas:
            if lista not in asignadas:
                errores.append(f"{nombre}: falta lista obligatoria '{lista}'")

        comentario = str(estrategia.get("primer_comentario_whatsapp", ""))
        if "{WHATSAPP_NUMERO}" in comentario or "XXXXXXXX" in comentario:
            advertencias.append(f"{nombre}: comentario de WhatsApp pendiente de numero")

    return {
        "ok": not errores,
        "fichas": len(fichas),
        "listas": len(nombres),
        "whatsapp_configurado": bool(whatsapp),
        "errores": errores,
        "advertencias": advertencias,
    }


def verificar(max_dias: float) -> dict:
    roles_cfg = leer_json(ROLES_FILE, {}) or {}
    # La revision de publicacion se ejecuta al final; se declara aqui para claridad.
    chain_cfg = leer_json(CHAIN_FILE, {}) or {}
    cadena = list(chain_cfg.get("orden", []))
    default_model = (leer_json(CONFIG, {}) or {}).get("model")

    errores_globales = []
    if not cadena:
        errores_globales.append("agents/modelos_gratuitos.json no tiene cadena de modelos")
    if default_model and default_model not in cadena:
        errores_globales.append(f"modelo por defecto fuera de la cadena gratuita: {default_model}")

    resultados = []
    for rol in roles_cfg.get("roles", []):
        rid = rol.get("id", "?")
        errores = []
        advertencias = []
        detalles = {}

        archivo_agente = AGENTS_DIR / f"{rid}.md"
        modelo = modelo_agente(archivo_agente)
        if not archivo_agente.exists():
            errores.append(f"falta definicion .opencode/agents/{rid}.md")
        elif not modelo:
            errores.append("la definicion no declara modelo")
        elif modelo not in cadena:
            errores.append(f"modelo fuera de la cadena gratuita: {modelo}")
        detalles["modelo"] = modelo

        for rel in rol.get("requeridos", []):
            ruta = ROOT / rel
            if not ruta.exists():
                errores.append(f"falta archivo requerido: {rel}")
            elif ruta.suffix in {".sh", ".py"}:
                ok, msg = revisar_sintaxis(ruta)
                if not ok:
                    errores.append(f"sintaxis invalida en {rel}: {msg.splitlines()[-1] if msg else ''}")

        for rel in rol.get("generados", []):
            if not (ROOT / rel).exists():
                advertencias.append(f"aun no generado: {rel}")

        estado_rol = None
        status_rel = rol.get("status")
        if status_rel:
            status_path = ROOT / status_rel
            if not status_path.exists():
                advertencias.append(f"sin archivo de estado: {status_rel}")
            else:
                estado_rol = leer_json(status_path)
                if not isinstance(estado_rol, dict):
                    advertencias.append(f"estado ilegible: {status_rel}")
                else:
                    state = str(estado_rol.get("state", "")).upper()
                    if "ERROR" in state or state == "FAIL":
                        errores.append(f"estado en error: {status_rel} ({state})")
                    dias = edad_dias(estado_rol.get("updated"))
                    if dias is None:
                        advertencias.append(f"estado sin fecha: {status_rel}")
                    elif dias > max_dias:
                        advertencias.append(
                            f"estado con {dias:.0f} dias de antiguedad: {status_rel}"
                        )
                    detalles["estado"] = state or "SIN_ESTADO"
        else:
            detalles["estado"] = "N/A"

        resultados.append({
            "id": rid,
            "nombre": rol.get("nombre", rid),
            "funcion": rol.get("funcion", ""),
            "critico": bool(rol.get("critico", False)),
            "modelo": modelo,
            "estado": detalles.get("estado"),
            "ok": not errores,
            "errores": errores,
            "advertencias": advertencias,
        })

    errores_globales.extend(
        f"{r['id']}: {e}" for r in resultados for e in r["errores"] if r["critico"]
    )
    roles_ok = sum(1 for r in resultados if r["ok"])
    advertencias = [f"{r['id']}: {a}" for r in resultados for a in r["advertencias"]]

    publicacion = verificar_publicacion()
    errores_globales.extend(f"publicacion: {e}" for e in publicacion["errores"])
    advertencias.extend(f"publicacion: {a}" for a in publicacion["advertencias"])

    ok = not errores_globales

    return {
        "state": "DONE" if ok else "ERROR",
        "ok": ok,
        "roles_total": len(resultados),
        "roles_ok": roles_ok,
        "errores": errores_globales,
        "advertencias": advertencias,
        "modelo_default": default_model,
        "modelos_gratuitos": len(cadena),
        "roles": resultados,
        "publicacion": publicacion,
        "updated": ahora(),
    }


def imprimir(resultado: dict) -> None:
    print(f"Agentes: {resultado['roles_ok']}/{resultado['roles_total']} OK")
    print(f"Modelo por defecto: {resultado['modelo_default']} (cadena gratuita: {resultado['modelos_gratuitos']})")
    print("-" * 78)
    for rol in resultado["roles"]:
        marca = "OK  " if rol["ok"] else "FALLA"
        print(f"[{marca}] {rol['id']:<22} {rol.get('modelo') or '-':<42} {rol.get('estado') or '-'}")
        for err in rol["errores"]:
            print(f"         error: {err}")
        for adv in rol["advertencias"]:
            print(f"         aviso: {adv}")
    pub = resultado.get("publicacion", {})
    print(
        f"Publicacion: {pub.get('fichas', 0)} fichas | {pub.get('listas', 0)} listas | "
        f"WhatsApp configurado: {'si' if pub.get('whatsapp_configurado') else 'no'}"
    )
    print("-" * 78)
    print(f"Estado: {resultado['state']} | errores: {len(resultado['errores'])} | avisos: {len(resultado['advertencias'])}")
    if resultado["errores"]:
        print("Errores globales:")
        for err in resultado["errores"]:
            print(f"  - {err}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificador de agentes de MGP Prospeccion")
    parser.add_argument("--json", action="store_true", help="salida en JSON")
    parser.add_argument("--max-dias", type=float, default=45.0, help="antiguedad maxima del estado (dias)")
    args = parser.parse_args()

    resultado = verificar(args.max_dias)
    escribir_json(STATUS_DIR / "agentes.json", resultado)
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        imprimir(resultado)
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
