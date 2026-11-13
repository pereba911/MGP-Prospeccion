#!/usr/bin/env python3
"""Dashboard local de MGP Prospeccion.

Corre en la Mac y consulta la VM de publicacion por SSH. No expone el token.
Abrir con doble clic en dashboard.command o:

    python3 dashboard_server.py
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
SSH_TARGET = os.environ.get("MGP_SSH_TARGET", "root@138.197.15.61")
REMOTE_DIR = os.environ.get("MGP_REMOTE_DIR", "/home/poster/mgp-prospeccion")
PORT = int(os.environ.get("MGP_PORT", "8765"))
SSH_OPTS = [
    "ssh", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=accept-new",
    "-o", "ConnectTimeout=8", "-o", "ServerAliveInterval=5", SSH_TARGET,
]

_lock = threading.Lock()
_cache: dict = {"ts": 0.0, "data": None}
CACHE_TTL = 3.0
SECRET_RE = re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+)")


def redact(text: str) -> str:
    return SECRET_RE.sub("***REDACTED***", text or "")


def ssh(script: str, timeout: int = 40, stdin: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        SSH_OPTS + ["python3", "-"],
        input=script if stdin is None else stdin,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


STATUS_SCRIPT = r'''
import json, os, re, subprocess

BASE = os.environ.get("MGP_REMOTE_DIR", "/home/poster/mgp-prospeccion")
os.chdir(BASE)

def sh(cmd, timeout=12):
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return (p.stdout or "").strip()
    except Exception:
        return ""

def redact(s):
    return re.sub(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+)", "***REDACTED***", s or "")

out = {}
out["host"] = sh("hostname")
out["time"] = sh("date '+%Y-%m-%d %H:%M:%S'")
out["uptime"] = sh("uptime -p")
cron = sh("crontab -l")
out["cron"] = {
    "autopush": "autopush.sh" in cron,
    "alert_bot": "alert_bot.sh" in cron,
    "token_in_cron": "GITHUB_TOKEN=" in cron,
}
out["token_env_file"] = os.path.isfile(".env") and os.path.getsize(".env") > 0

log = sh("git log -1 --format='%h|%ci|%s'")
parts = log.split("|", 2)
out["git"] = {
    "head": parts[0] if parts else "",
    "date": parts[1] if len(parts) > 1 else "",
    "subject": parts[2] if len(parts) > 2 else "",
}
ab = sh("git rev-list --left-right --count origin/main...HEAD").split()
out["git"]["ahead"] = int(ab[1]) if len(ab) > 1 and ab[1].isdigit() else None
out["git"]["behind"] = int(ab[0]) if ab and ab[0].isdigit() else None
out["git"]["dirty"] = bool(sh("git status --porcelain"))

names = ["repo_init", "autopush_builder", "data_collector", "content_gen_1",
         "content_gen_2", "content_gen_3", "scheduler_validator", "alert_bot"]
st = {}
for n in names:
    try:
        with open(os.path.join(BASE, "status", n + ".json"), encoding="utf-8") as fh:
            st[n] = json.load(fh)
    except Exception:
        st[n] = None
out["statuses"] = st

out["portal_data"] = os.path.isfile("portal_data.json")
batches = []
for n in (1, 2, 3):
    p = os.path.join(BASE, "fotos_batch", "batch-%d" % n, "lista.txt")
    try:
        batches.append(len([l for l in open(p, encoding="utf-8") if l.strip()]))
    except Exception:
        batches.append(0)
out["batches"] = batches
out["fotos_total"] = int(sh("find propiedades -type f \\( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \\) -not -path '*/fotografias_procesadas/*' | wc -l") or 0)
out["fotos_procesadas"] = int(sh("find propiedades -type f -path '*/fotografias_procesadas/*' \\( -iname '*.jpg' -o -iname '*.jpeg' -o -iname '*.png' \\) | wc -l") or 0)
out["chrome"] = bool(sh("pgrep -f 'load-extension=/home/poster/multigroup-extension' | head -1"))
out["disk"] = sh("df -h / | tail -1")

def tail(path, n=30):
    return redact(sh("tail -n %d '%s' 2>/dev/null" % (n, path)))

out["logs"] = {
    "autopush": tail(os.path.join(BASE, "autopush.log"), 30),
    "alertas": tail(os.path.join(BASE, "alertas.log"), 40),
}
out["last_error"] = redact(sh("grep -E 'rejected|GH013|fatal:|error:' autopush.log 2>/dev/null | tail -1"))
print(json.dumps(out, ensure_ascii=False))
'''


def get_status(force: bool = False) -> dict:
    with _lock:
        if not force and _cache["data"] and (time.time() - _cache["ts"]) < CACHE_TTL:
            return _cache["data"]
    try:
        proc = ssh(f'import os; os.environ["MGP_REMOTE_DIR"]={REMOTE_DIR!r}\n' + STATUS_SCRIPT, timeout=35)
        if proc.returncode != 0:
            raise RuntimeError(redact(proc.stderr.strip()) or "SSH fallo")
        data = json.loads(proc.stdout.strip().splitlines()[-1])
        data["ok"] = True
        data["checked_at"] = time.strftime("%H:%M:%S")
    except Exception as exc:  # noqa: BLE001
        data = {"ok": False, "error": redact(str(exc)), "checked_at": time.strftime("%H:%M:%S")}
    with _lock:
        _cache["ts"] = time.time()
        _cache["data"] = data
    return data


AUTOPUSH_CRON = "0 10 * * 1 {base}/autopush.sh >> {base}/autopush.log 2>&1"
ALERT_CRON = "*/5 * * * * {base}/alert_bot.sh >> {base}/alert_bot.log 2>&1"


def action_cron(enable: bool) -> dict:
    script = f'''
import subprocess
BASE = {REMOTE_DIR!r}
cur = subprocess.run(["crontab", "-l"], capture_output=True, text=True).stdout
lines = cur.splitlines()
keep = [l for l in lines if "autopush.sh" not in l and "alert_bot.sh" not in l]
if {enable!r}:
    keep += [
        {AUTOPUSH_CRON.format(base=REMOTE_DIR)!r},
        {ALERT_CRON.format(base=REMOTE_DIR)!r},
    ]
new = "\\n".join([l for l in keep if l.strip()]) + "\\n"
subprocess.run(["crontab", "-"], input=new, text=True, check=True)
print("Automatizacion activada" if {enable!r} else "Automatizacion detenida")
'''
    proc = ssh(script, timeout=20)
    return {
        "ok": proc.returncode == 0,
        "output": redact((proc.stdout + proc.stderr).strip()),
    }


def action_run(command: str, timeout: int) -> dict:
    script = f'''
import subprocess
p = subprocess.run({command!r}, shell=True, cwd={REMOTE_DIR!r},
                   capture_output=True, text=True, timeout={timeout - 5})
print(p.stdout)
print(p.stderr)
raise SystemExit(p.returncode)
'''
    try:
        proc = ssh(script, timeout=timeout)
        return {
            "ok": proc.returncode == 0,
            "output": redact((proc.stdout + proc.stderr).strip())[-4000:],
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "output": f"Tiempo agotado ({timeout}s)"}


def action_set_token(token: str) -> dict:
    token = token.strip()
    if not re.fullmatch(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]+)", token):
        return {"ok": False, "output": "Formato de token invalido"}
    script = f'''
import os
BASE = {REMOTE_DIR!r}
path = os.path.join(BASE, ".env")
with open(path, "w", encoding="utf-8") as fh:
    fh.write("GITHUB_TOKEN=%s\\n" % {token!r})
os.chmod(path, 0o600)
print("Token actualizado en .env (600)")
'''
    proc = ssh(script, timeout=15)
    return {"ok": proc.returncode == 0, "output": redact((proc.stdout + proc.stderr).strip())}


class Handler(BaseHTTPRequestHandler):
    server_version = "MGPDashboard/1.0"

    def log_message(self, fmt, *args):  # silencio en consola
        return

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data: dict, code: int = 200) -> None:
        self._send(code, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html", "/dashboard.html"):
            html = (BASE_DIR / "dashboard.html").read_bytes()
            self._send(200, html, "text/html; charset=utf-8")
            return
        if parsed.path == "/api/status":
            force = parse_qs(parsed.query).get("refresh") == ["1"]
            self._json(get_status(force=force))
            return
        self._json({"ok": False, "error": "No encontrado"}, 404)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            payload = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            payload = {}

        if parsed.path == "/api/automation":
            enable = bool(payload.get("enable"))
            result = action_cron(enable)
        elif parsed.path == "/api/run":
            accion = payload.get("action")
            comandos = {
                "autopush": ("bash autopush.sh", 90),
                "sync": ("python3 actualizar_propiedades_marketplace.py", 180),
                "fotos": ("python3 procesar_fotos.py --todo", 300),
                "validar": (
                    "bash -n autopush.sh && bash -n alert_bot.sh && "
                    "echo 'sintaxis OK'; "
                    "(crontab -l | grep -c autopush.sh) | xargs -I{} echo 'cron autopush: {}'; "
                    "(crontab -l | grep -c alert_bot.sh) | xargs -I{} echo 'cron alert_bot: {}'",
                    30,
                ),
            }
            if accion not in comandos:
                self._json({"ok": False, "output": "Accion desconocida"}, 400)
                return
            cmd, timeout = comandos[accion]
            result = action_run(cmd, timeout)
        elif parsed.path == "/api/token":
            result = action_set_token(str(payload.get("token", "")))
        else:
            self._json({"ok": False, "error": "No encontrado"}, 404)
            return

        with _lock:
            _cache["ts"] = 0.0
        self._json(result)


def main() -> None:
    try:
        server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    except OSError as exc:
        print(f"No se pudo abrir el puerto {PORT}: {exc}")
        print(f"Quizas ya esta corriendo: http://127.0.0.1:{PORT}")
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        return

    url = f"http://127.0.0.1:{PORT}"
    print("=" * 60)
    print("  MGP Prospeccion - Dashboard local")
    print(f"  {url}   (Ctrl+C para detener)")
    print("=" * 60)
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard detenido.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
