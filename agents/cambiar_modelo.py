#!/usr/bin/env python3
"""Cambia el modelo de OpenCode y de los agentes del proyecto sin costo adicional.

Todos los modelos de agents/modelos_gratuitos.json tienen costo 0. El script
solo permite elegir dentro de esa cadena, para que un cambio por cuota agotada
nunca termine usando un modelo de pago.

Uso:
    python3 agents/cambiar_modelo.py --estado
    python3 agents/cambiar_modelo.py --siguiente --motivo "cuota agotada"
    python3 agents/cambiar_modelo.py --modelo opencode/glm-5.3-flash-free
    python3 agents/cambiar_modelo.py --rol content-gen-1 --siguiente
    python3 agents/cambiar_modelo.py --verificar
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / ".opencode" / "opencode.jsonc"
AGENTS_DIR = ROOT / ".opencode" / "agents"
CHAIN_FILE = ROOT / "agents" / "modelos_gratuitos.json"
STATUS_DIR = ROOT / "status"

MODELO_RE = re.compile(r"^model:\s*(\S+)\s*$", re.MULTILINE)


def ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def leer_json(ruta: Path) -> dict:
    with ruta.open(encoding="utf-8") as fh:
        return json.load(fh)


def escribir_json(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cargar_cadena() -> dict:
    if not CHAIN_FILE.exists():
        raise SystemExit(f"No existe {CHAIN_FILE}")
    return leer_json(CHAIN_FILE)


def cadena(cfg: dict) -> list[str]:
    return list(cfg.get("orden", []))


def modelo_actual_config() -> str | None:
    if not CONFIG.exists():
        return None
    try:
        return leer_json(CONFIG).get("model")
    except json.JSONDecodeError:
        return None


def agente_archivo(rol: str) -> Path:
    return AGENTS_DIR / f"{rol}.md"


def leer_modelo_agente(ruta: Path) -> str | None:
    if not ruta.exists():
        return None
    texto = ruta.read_text(encoding="utf-8")
    if not texto.startswith("---"):
        return None
    fin = texto.find("\n---", 3)
    if fin == -1:
        return None
    bloque = texto[:fin]
    match = MODELO_RE.search(bloque)
    return match.group(1) if match else None


def escribir_modelo_agente(ruta: Path, modelo: str) -> bool:
    if not ruta.exists():
        return False
    texto = ruta.read_text(encoding="utf-8")
    if not texto.startswith("---"):
        return False
    fin = texto.find("\n---", 3)
    if fin == -1:
        return False
    bloque, resto = texto[:fin], texto[fin:]
    if MODELO_RE.search(bloque):
        bloque = MODELO_RE.sub(f"model: {modelo}", bloque, count=1)
    else:
        bloque = bloque.rstrip() + f"\nmodel: {modelo}"
    ruta.write_text(bloque + resto, encoding="utf-8")
    return True


def escribir_modelo_config(modelo: str) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    datos = {}
    if CONFIG.exists():
        try:
            datos = leer_json(CONFIG)
        except json.JSONDecodeError:
            datos = {}
    datos["$schema"] = datos.get(
        "$schema", "https://opencode.ai/config.json"
    )
    datos["model"] = modelo
    CONFIG.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def siguiente_en_cadena(modelo: str | None, cadena_modelos: list[str]) -> str:
    if not cadena_modelos:
        raise SystemExit("La cadena de modelos gratuitos esta vacia")
    if modelo in cadena_modelos:
        return cadena_modelos[(cadena_modelos.index(modelo) + 1) % len(cadena_modelos)]
    return cadena_modelos[0]


def validar(modelo: str, cadena_modelos: list[str]) -> None:
    if modelo not in cadena_modelos:
        raise SystemExit(
            f"Modelo no permitido: {modelo}\n"
            "Solo se aceptan modelos de agents/modelos_gratuitos.json (costo 0)."
        )


def estado() -> dict:
    cfg = cargar_cadena()
    cadena_modelos = cadena(cfg)
    agentes = {}
    for ruta in sorted(AGENTS_DIR.glob("*.md")):
        agentes[ruta.stem] = leer_modelo_agente(ruta)
    default = modelo_actual_config()
    fuera = []
    if default and default not in cadena_modelos:
        fuera.append({"destino": "config", "modelo": default})
    for rol, modelo in agentes.items():
        if modelo not in cadena_modelos:
            fuera.append({"destino": rol, "modelo": modelo})
    return {
        "default": default,
        "agentes": agentes,
        "cadena": cadena_modelos,
        "fuera_de_cadena": fuera,
        "todo_gratuito": not fuera,
        "actualizado": ahora(),
    }


def registrar(datos: dict) -> None:
    ruta = STATUS_DIR / "modelos.json"
    historial = []
    if ruta.exists():
        try:
            historial = leer_json(ruta).get("historial", [])
        except json.JSONDecodeError:
            historial = []
    historial.append(datos)
    escribir_json(ruta, {
        "state": "DONE",
        "default": datos.get("default"),
        "todo_gratuito": datos.get("todo_gratuito", True),
        "actualizado": ahora(),
        "historial": historial[-25:],
    })


def aplicar(modelo: str, cfg: dict, rol: str | None, motivo: str, rotar: bool) -> dict:
    cadena_modelos = cadena(cfg)
    validar(modelo, cadena_modelos)
    cambios = {}

    if rol:
        ruta = agente_archivo(rol)
        if not ruta.exists():
            raise SystemExit(f"No existe el agente {ruta}")
        if not escribir_modelo_agente(ruta, modelo):
            raise SystemExit(f"No se pudo editar el frontmatter de {ruta}")
        cambios[rol] = modelo
        escribir_modelo_config(modelo_actual_config() or modelo)
    else:
        escribir_modelo_config(modelo)
        cambios["default"] = modelo
        for ruta in sorted(AGENTS_DIR.glob("*.md")):
            actual = leer_modelo_agente(ruta)
            nuevo = siguiente_en_cadena(actual, cadena_modelos) if rotar else modelo
            if escribir_modelo_agente(ruta, nuevo):
                cambios[ruta.stem] = nuevo

    cfg.setdefault("roles", {})
    for nombre, valor in cambios.items():
        if nombre != "default":
            cfg["roles"][nombre] = valor
    escribir_json(CHAIN_FILE, cfg)

    resultado = {
        "state": "DONE",
        "motivo": motivo,
        "default": modelo_actual_config(),
        "cambios": cambios,
        "todo_gratuito": True,
        "actualizado": ahora(),
    }
    registrar(resultado)
    return resultado


def main() -> int:
    parser = argparse.ArgumentParser(description="Conmutador de modelos gratuitos de MGP Prospeccion")
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--estado", action="store_true", help="muestra el modelo actual de cada agente")
    grupo.add_argument("--siguiente", action="store_true", help="pasa al siguiente modelo gratuito de la cadena")
    grupo.add_argument("--modelo", help="fija un modelo gratuito concreto (provider/model)")
    grupo.add_argument("--verificar", action="store_true", help="valida que todo este dentro de la cadena gratuita")
    parser.add_argument("--rol", help="aplica el cambio solo a un agente, por ejemplo content-gen-1")
    parser.add_argument("--motivo", default="cambio manual", help="motivo del cambio para el historial")
    parser.add_argument("--json", action="store_true", help="salida en JSON")
    args = parser.parse_args()

    cfg = cargar_cadena()

    if args.estado or args.verificar:
        datos = estado()
        if args.json:
            print(json.dumps(datos, ensure_ascii=False, indent=2))
        else:
            print(f"Modelo por defecto: {datos['default']}")
            print("Agentes:")
            for rol, modelo in datos["agentes"].items():
                print(f"  {rol:<24} {modelo}")
            print(f"Todo con costo 0: {'si' if datos['todo_gratuito'] else 'NO'}")
            if datos["fuera_de_cadena"]:
                print("Fuera de la cadena gratuita:")
                for item in datos["fuera_de_cadena"]:
                    print(f"  {item['destino']}: {item['modelo']}")
        return 0 if datos["todo_gratuito"] else 1

    if args.modelo:
        modelo = args.modelo
    else:
        base = leer_modelo_agente(agente_archivo(args.rol)) if args.rol else modelo_actual_config()
        modelo = siguiente_en_cadena(base, cadena(cfg))

    resultado = aplicar(modelo, cfg, args.rol, args.motivo, rotar=args.siguiente)
    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        print(f"Modelo aplicado: {resultado['default']}")
        for destino, valor in resultado["cambios"].items():
            print(f"  {destino:<24} {valor}")
        print("Todos los modelos tienen costo 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
