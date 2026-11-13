#!/usr/bin/env python3
"""Envia alertas de MGP Prospeccion a WhatsApp.

Proveedores soportados:
  callmebot  Gratuito. Requiere CALLMEBOT_APIKEY y el numero registrado.
  meta       WhatsApp Cloud API oficial. Requiere META_WA_TOKEN y META_WA_PHONE_ID.

La configuracion vive en .env (permisos 600), nunca en el repositorio.
Si no hay credenciales, el script no falla: informa "sin_configurar".

Uso:
    python3 agents/notificar_whatsapp.py --texto "mensaje"
    python3 agents/notificar_whatsapp.py --probar
    python3 agents/notificar_whatsapp.py --estado
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = ROOT / ".env"
STATUS = ROOT / "status" / "whatsapp.json"
SECRET_RE = re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")
MAX_LARGO = 1200


def ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def cargar_env() -> None:
    """Carga .env sin sobrescribir variables ya definidas en el entorno."""
    if not ENV_FILE.exists():
        return
    for linea in ENV_FILE.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = linea.split("=", 1)
        clave = clave.strip()
        valor = valor.strip().strip("'\"")
        if clave and clave not in os.environ:
            os.environ[clave] = valor


def limpiar(texto: str) -> str:
    texto = SECRET_RE.sub("[credencial oculta]", texto)
    texto = texto.strip()
    return texto[:MAX_LARGO]


def config() -> dict:
    proveedor = os.environ.get("WHATSAPP_PROVIDER", "").strip().lower()
    destino = re.sub(r"\D", "", os.environ.get("WHATSAPP_ALERTAS", ""))
    return {
        "proveedor": proveedor,
        "destino": destino,
        "callmebot_apikey": os.environ.get("CALLMEBOT_APIKEY", "").strip(),
        "meta_token": os.environ.get("META_WA_TOKEN", "").strip(),
        "meta_phone_id": os.environ.get("META_WA_PHONE_ID", "").strip(),
    }


def proveedor_efectivo(cfg: dict) -> str:
    if cfg["proveedor"] in {"callmebot", "meta"}:
        return cfg["proveedor"]
    if cfg["callmebot_apikey"]:
        return "callmebot"
    if cfg["meta_token"] and cfg["meta_phone_id"]:
        return "meta"
    return ""


def enviar_callmebot(cfg: dict, texto: str) -> tuple[bool, str]:
    datos = urllib.parse.urlencode({
        "phone": "+" + cfg["destino"],
        "text": texto,
        "apikey": cfg["callmebot_apikey"],
    }).encode()
    req = urllib.request.Request(
        "https://api.callmebot.com/whatsapp.php",
        data=datos,
        headers={"User-Agent": "MGP-Prospeccion/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        cuerpo = resp.read().decode("utf-8", errors="replace")
    bajo = cuerpo.lower()
    ok = resp.status == 200 and not any(
        x in bajo for x in ("error", "invalid", "not allowed", "not registered")
    )
    return ok, "enviado" if ok else "respuesta no valida de CallMeBot"


def enviar_meta(cfg: dict, texto: str) -> tuple[bool, str]:
    url = f"https://graph.facebook.com/v21.0/{cfg['meta_phone_id']}/messages"
    cuerpo = json.dumps({
        "messaging_product": "whatsapp",
        "to": cfg["destino"],
        "type": "text",
        "text": {"body": texto},
    }).encode()
    req = urllib.request.Request(
        url,
        data=cuerpo,
        headers={
            "Authorization": f"Bearer {cfg['meta_token']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp.read()
        return True, "enviado"
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode("utf-8", errors="replace")
        return False, f"Meta HTTP {exc.code}: {detalle[:200]}"


def registrar(resultado: dict) -> None:
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


def enviar(texto: str, prueba: bool = False) -> dict:
    cfg = config()
    proveedor = proveedor_efectivo(cfg)
    resultado = {
        "state": "DONE",
        "proveedor": proveedor or None,
        "destino_configurado": bool(cfg["destino"]),
        "prueba": prueba,
        "updated": ahora(),
    }

    if not cfg["destino"]:
        resultado.update(state="SIN_CONFIGURAR", detalle="falta WHATSAPP_ALERTAS")
        return resultado
    if not proveedor:
        resultado.update(state="SIN_CONFIGURAR", detalle="faltan credenciales del proveedor")
        return resultado

    texto = limpiar(texto)
    try:
        if proveedor == "callmebot":
            if not cfg["callmebot_apikey"]:
                resultado.update(state="SIN_CONFIGURAR", detalle="falta CALLMEBOT_APIKEY")
                return resultado
            ok, detalle = enviar_callmebot(cfg, texto)
        else:
            if not (cfg["meta_token"] and cfg["meta_phone_id"]):
                resultado.update(state="SIN_CONFIGURAR", detalle="faltan META_WA_TOKEN o META_WA_PHONE_ID")
                return resultado
            ok, detalle = enviar_meta(cfg, texto)
    except Exception as exc:  # noqa: BLE001
        ok, detalle = False, SECRET_RE.sub("[credencial oculta]", str(exc))[:200]

    resultado.update(state="DONE" if ok else "ERROR", detalle=detalle)
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(description="Notificador de WhatsApp para MGP")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--texto", help="mensaje a enviar")
    grupo.add_argument("--probar", action="store_true", help="envia un mensaje de prueba")
    grupo.add_argument("--estado", action="store_true", help="solo muestra la configuracion")
    parser.add_argument("--json", action="store_true", help="salida en JSON")
    args = parser.parse_args()
    cargar_env()

    if args.estado:
        cfg = config()
        datos = {
            "proveedor": proveedor_efectivo(cfg) or None,
            "destino_configurado": bool(cfg["destino"]),
            "callmebot_configurado": bool(cfg["callmebot_apikey"]),
            "meta_configurado": bool(cfg["meta_token"] and cfg["meta_phone_id"]),
        }
        print(json.dumps(datos, ensure_ascii=False, indent=2) if args.json else datos)
        return 0

    texto = args.texto or "[MGP-Prospeccion] Prueba de alertas por WhatsApp. La configuracion funciona."
    resultado = enviar(texto, prueba=args.probar)
    registrar(resultado)

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False))
    else:
        print(resultado["state"] + (f": {resultado.get('detalle')}" if resultado.get("detalle") else ""))
    return 0 if resultado["state"] in {"DONE", "SIN_CONFIGURAR"} else 1


if __name__ == "__main__":
    sys.exit(main())
