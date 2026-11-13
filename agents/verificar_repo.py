#!/usr/bin/env python3
"""Revisa la salud basica del repositorio y escribe status/repo_init.json.

Comprueba rama, remoto, .gitignore, documentacion base y que no haya
credenciales versionadas. No imprime ningun valor sensible.

Uso:
    python3 agents/verificar_repo.py
    python3 agents/verificar_repo.py --json
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
STATUS = ROOT / "status" / "repo_init.json"
GITIGNORE = ROOT / ".gitignore"
DOC = ROOT / "MANUAL_RAPIDO.md"
SECRET_RE = re.compile(r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}")
REQUIRED_IGNORES = [".env", "status/", "autopush.log", "alert_bot.log", "alertas.log"]


def ahora() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True
    )
    return proc.stdout.strip() if proc.returncode == 0 else ""


def revisar() -> dict:
    errores: list[str] = []
    avisos: list[str] = []

    rama = git("rev-parse", "--abbrev-ref", "HEAD")
    if rama != "main":
        errores.append(f"la rama actual es '{rama or 'desconocida'}', se esperaba 'main'")

    remotos = git("remote").splitlines()
    if "origin" not in remotos:
        errores.append("no existe el remoto origin")
    url = git("remote", "get-url", "origin")
    if url and "github.com" not in url:
        avisos.append("el remoto origin no apunta a github.com")

    if not GITIGNORE.exists():
        errores.append("falta .gitignore")
    else:
        lineas = {l.strip() for l in GITIGNORE.read_text(encoding="utf-8").splitlines()}
        faltan = [p for p in REQUIRED_IGNORES if p not in lineas]
        if faltan:
            errores.append(".gitignore no excluye: " + ", ".join(faltan))

    if not DOC.exists():
        errores.append("falta MANUAL_RAPIDO.md")

    versionados = git("ls-files").splitlines()
    sospechosos = []
    for rel in versionados:
        ruta = ROOT / rel
        if not ruta.is_file() or ruta.stat().st_size > 2_000_000:
            continue
        try:
            texto = ruta.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if SECRET_RE.search(texto):
            sospechosos.append(rel)
    if sospechosos:
        errores.append("posible credencial en archivos versionados: " + ", ".join(sospechosos))

    pendientes = git("status", "--porcelain")
    if pendientes:
        avisos.append(f"hay {len(pendientes.splitlines())} cambios locales sin confirmar")

    return {
        "state": "DONE" if not errores else "ERROR",
        "ok": not errores,
        "rama": rama,
        "remoto": url,
        "documentacion": DOC.exists(),
        "credenciales_versionadas": sospechosos,
        "errores": errores,
        "advertencias": avisos,
        "updated": ahora(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Revision basica del repositorio MGP")
    parser.add_argument("--json", action="store_true", help="salida en JSON")
    args = parser.parse_args()

    resultado = revisar()
    STATUS.parent.mkdir(parents=True, exist_ok=True)
    STATUS.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        print(f"Repo: {resultado['state']} | rama {resultado['rama']} | {resultado['remoto']}")
        for err in resultado["errores"]:
            print(f"  error: {err}")
        for adv in resultado["advertencias"]:
            print(f"  aviso: {adv}")
    return 0 if resultado["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
