#!/usr/bin/env python3
"""
Despachador Autónomo de Publicaciones Diarias para MultiGroup Poster.

Determina el día de la semana, selecciona las propiedades y variantes según
el calendario de rotación, prepara el plan de publicación (fotos, copys, listas),
asegura que el canal de control y el agente de Chrome estén activos, y ejecuta
el plan respetando la regla de idempotencia para no duplicar publicaciones.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

BASE_DIR = Path(__file__).resolve().parent
CONTROL_DIR = Path("/home/poster/control")
if not CONTROL_DIR.exists():
    CONTROL_DIR = BASE_DIR / "control"
STATUS_FILE = BASE_DIR / "status" / "despachador.json"
CONFIG_FILE = BASE_DIR / "config_publicacion.json"

ROTACION_SEMANAL = {
    0: {  # Lunes
        "nombre": "Lunes",
        "tipo": "Venta",
        "propiedades": ["01_colinas_san_javier_casa_venta", "02_country_club_depto_venta"],
        "listas": ["Solo Venta"],
        "variante": "variante_1_ejecutiva.txt",
        "wait_minutes": 2.5,
        "max_posts": 25,
    },
    1: {  # Martes
        "nombre": "Martes",
        "tipo": "Renta",
        "propiedades": [
            "03_elysian_country_amueblado_renta",
            "04_country_club_200m2_renta",
            "05_torre_opera_depto_renta",
            "06_hyatt_regency_andares_renta",
            "07_torre_hsbc_oficinas_renta",
            "08_americana_estudio_amueblado_renta",
        ],
        "listas": ["Lista Venta y Renta"],
        "variante": "variante_1_ejecutiva.txt",
        "wait_minutes": 2.5,
        "max_posts": 25,
    },
    2: {  # Miércoles
        "nombre": "Miércoles",
        "tipo": "Refuerzo",
        "propiedades": ["01_colinas_san_javier_casa_venta"],
        "listas": ["Solo Venta"],
        "variante": "variante_3_inversion.txt",
        "wait_minutes": 2.5,
        "max_posts": 25,
    },
    3: {  # Jueves
        "nombre": "Jueves",
        "tipo": "Venta",
        "propiedades": ["01_colinas_san_javier_casa_venta", "02_country_club_depto_venta"],
        "listas": ["Solo Venta"],
        "variante": "variante_2_estilo_vida.txt",
        "wait_minutes": 2.5,
        "max_posts": 25,
    },
    4: {  # Viernes
        "nombre": "Viernes",
        "tipo": "Renta",
        "propiedades": [
            "03_elysian_country_amueblado_renta",
            "04_country_club_200m2_renta",
            "05_torre_opera_depto_renta",
            "06_hyatt_regency_andares_renta",
            "07_torre_hsbc_oficinas_renta",
            "08_americana_estudio_amueblado_renta",
        ],
        "listas": ["Lista Venta y Renta"],
        "variante": "variante_2_estilo_vida.txt",
        "wait_minutes": 2.5,
        "max_posts": 25,
    },
    5: {  # Sábado
        "nombre": "Sábado",
        "tipo": "Especial",
        "propiedades": ["07_torre_hsbc_oficinas_renta"],
        "listas": ["Terrenos Vta"],
        "variante": "variante_3_inversion.txt",
        "wait_minutes": 3.0,
        "max_posts": 20,
    },
    6: {  # Domingo
        "nombre": "Domingo",
        "tipo": "Descanso",
        "propiedades": [],
        "listas": [],
        "variante": None,
        "wait_minutes": 0,
        "max_posts": 0,
    },
}


def obtener_contacto_whatsapp() -> str:
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            num = data.get("whatsapp_numero", "").strip()
            if num:
                return f"Informes y citas directas por WhatsApp: https://wa.me/{num}"
        except Exception:
            pass
    return "Informes y citas directas por mensaje o llamada."


def obtener_fotos_propiedad(prop_dir: Path, max_fotos: int = 6) -> list[str]:
    fotos_dir = prop_dir / "fotografias"
    if not fotos_dir.exists():
        return []
    valid_exts = {".jpg", ".jpeg", ".png"}
    fotos = [
        f for f in sorted(os.listdir(fotos_dir))
        if Path(f).suffix.lower() in valid_exts and not f.startswith(".")
    ]
    # Retornar rutas relativas al repositorio
    rel_base = prop_dir.relative_to(BASE_DIR) if BASE_DIR in prop_dir.parents else Path("propiedades") / prop_dir.name
    return [str(rel_base / "fotografias" / f) for f in fotos[:max_fotos]]


def obtener_texto_propiedad(prop_dir: Path, variante_file: str) -> str:
    desc_dir = prop_dir / "descripciones"
    v_path = desc_dir / variante_file
    if v_path.exists():
        return v_path.read_text(encoding="utf-8").strip()
    # Si no existe la variante pedida, tomar el primer archivo .txt
    txt_files = [f for f in os.listdir(desc_dir) if f.endswith(".txt")] if desc_dir.exists() else []
    if txt_files:
        return (desc_dir / sorted(txt_files)[0]).read_text(encoding="utf-8").strip()
    return f"Propiedad disponible en {prop_dir.name.replace('_', ' ').title()}."


def generar_plan_del_dia(dia_idx: int | None = None, propiedad_override: str | None = None) -> dict:
    ahora = datetime.now()
    if dia_idx is None:
        dia_idx = ahora.weekday()

    config_dia = ROTACION_SEMANAL.get(dia_idx, ROTACION_SEMANAL[6])
    fecha_str = ahora.strftime("%Y-%m-%d")
    run_id = f"mgp_{fecha_str}_{config_dia['nombre'].lower()}"

    if config_dia["tipo"] == "Descanso" and not propiedad_override:
        return {
            "runId": run_id,
            "dia": config_dia["nombre"],
            "fecha": fecha_str,
            "tipo": "Descanso",
            "nota": "Descanso algorítmico obligatorio. Cero publicaciones hoy.",
            "jobs": [],
        }

    props_target = [propiedad_override] if propiedad_override else config_dia["propiedades"]
    variante_file = config_dia["variante"] or "variante_1_ejecutiva.txt"
    comment = obtener_contacto_whatsapp()
    jobs = []

    for p_id in props_target:
        p_dir = BASE_DIR / "propiedades" / p_id
        if not p_dir.exists():
            continue
        texto = obtener_texto_propiedad(p_dir, variante_file)
        fotos = obtener_fotos_propiedad(p_dir, max_fotos=6)
        job_id = f"{fecha_str}_{p_id}"
        jobs.append({
            "id": job_id,
            "type": "publish",
            "property_id": p_id,
            "text": texto,
            "comment": comment,
            "photos": fotos,
            "lists": config_dia["listas"],
            "waitMinutes": config_dia["wait_minutes"],
            "method": "safe",
        })

    return {
        "runId": run_id,
        "dia": config_dia["nombre"],
        "fecha": fecha_str,
        "tipo": config_dia["tipo"],
        "jobs": jobs,
    }


def verificar_idempotencia_hoy(plan: dict) -> tuple[bool, str]:
    """Retorna (ya_ejecutado, motivo) según el historial registrado."""
    if not STATUS_FILE.exists():
        return False, "Sin ejecuciones previas registradas."
    try:
        prev = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
        if prev.get("fecha") == plan["fecha"] and prev.get("state") in ("DONE", "EN_CURSO"):
            # Verificar si los mismos jobs ya fueron ejecutados
            prev_jobs = prev.get("jobs_completados", [])
            plan_jobs = [j["id"] for j in plan.get("jobs", [])]
            if all(j in prev_jobs for j in plan_jobs) and plan_jobs:
                return True, f"Los jobs para {plan['fecha']} ya fueron procesados previamente ({len(prev_jobs)} completados)."
    except Exception:
        pass
    return False, "Pendiente de ejecución."


def asegurar_canal_control() -> bool:
    """Verifica si el servidor de control en 127.0.0.1:8899 está respondiendo."""
    try:
        req = urllib.request.urlopen("http://127.0.0.1:8899/health", timeout=3)
        return req.status == 200
    except Exception:
        # Intentar levantarlo si estamos en la VM
        srv_script = CONTROL_DIR / "server.py"
        if srv_script.exists():
            try:
                subprocess.Popen(
                    ["nohup", sys.executable, str(srv_script)],
                    cwd=str(CONTROL_DIR),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setpgrp if hasattr(os, "setpgrp") else None,
                )
                time.sleep(2)
                req = urllib.request.urlopen("http://127.0.0.1:8899/health", timeout=3)
                return req.status == 200
            except Exception:
                return False
        return False


def inyectar_agente_cdp() -> tuple[bool, str]:
    """Inyecta agent.js en Chrome vía CDP si no está activo, abriendo la pestaña si hace falta."""
    tools_dir = Path("/home/poster/tools")
    if not tools_dir.exists():
        return False, "tools_dir no existe en este entorno (solo aplica en la VM)."
    try:
        sys.path.insert(0, str(tools_dir))
        import cdp  # type: ignore

        agent_js_path = CONTROL_DIR / "agent.js"
        if not agent_js_path.exists():
            return False, f"No existe {agent_js_path}"

        ext_url = "chrome-extension://bffigfjkllaipccbpnmckgfhmdmlgdda/index.html"
        p = None
        try:
            p = cdp.conectar(ext_url)
        except Exception:
            # Abrir la pestaña si no estaba abierta
            try:
                open_url = f"http://127.0.0.1:9222/json/new?{ext_url}"
                req = urllib.request.Request(open_url, method="PUT")
                urllib.request.urlopen(req, timeout=5)
                time.sleep(2)
                p = cdp.conectar(ext_url)
            except Exception as e:
                return False, f"No se pudo abrir ni conectar a la pestaña de MGP: {e}"

        is_auto = p.eval("window.__mgpAuto")
        if is_auto:
            p.close()
            return True, "Agente ya estaba activo en Chrome."

        js_code = agent_js_path.read_text(encoding="utf-8")
        res = p.eval(js_code)
        p.close()
        return True, f"Agente inyectado exitosamente: {res}"
    except Exception as exc:
        return False, f"Fallo al conectar/inyectar vía CDP: {exc}"


def despachar(plan: dict, force: bool = False, dry_run: bool = False) -> dict:
    fecha_str = plan["fecha"]
    dia_nombre = plan["dia"]

    if plan["tipo"] == "Descanso":
        res = {
            "state": "DONE",
            "fecha": fecha_str,
            "dia": dia_nombre,
            "tipo": "Descanso",
            "mensaje": "Descanso algorítmico obligatorio (sin publicaciones).",
            "jobs_completados": [],
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        guardar_estado(res)
        return res

    ya_hecho, motivo = verificar_idempotencia_hoy(plan)
    if ya_hecho and not force:
        return {
            "state": "OMITIDO",
            "fecha": fecha_str,
            "dia": dia_nombre,
            "motivo": motivo,
            "jobs_completados": plan.get("jobs", []),
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    if dry_run:
        return {
            "state": "DRY_RUN_OK",
            "fecha": fecha_str,
            "dia": dia_nombre,
            "plan": plan,
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

    # 1. Asegurar servidor de control
    ctrl_ok = asegurar_canal_control()
    if not ctrl_ok:
        res = {
            "state": "ERROR",
            "error": "El servidor de control en 127.0.0.1:8899 no responde y no pudo iniciarse.",
            "fecha": fecha_str,
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        guardar_estado(res)
        return res

    # 2. Escribir plan.json
    plan_path = CONTROL_DIR / "plan.json"
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    # 3. Asegurar que agent.js esté inyectado
    inj_ok, inj_msg = inyectar_agente_cdp()

    # 4. Registrar estado en curso
    res = {
        "state": "EN_CURSO",
        "runId": plan["runId"],
        "fecha": fecha_str,
        "dia": dia_nombre,
        "tipo": plan["tipo"],
        "jobs_enviados": [j["id"] for j in plan["jobs"]],
        "detalles": [
            {
                "id": j["id"],
                "propiedad": j["property_id"],
                "fotos": len(j["photos"]),
                "listas": j["lists"],
                "wait": j["waitMinutes"],
            }
            for j in plan["jobs"]
        ],
        "control_http": ctrl_ok,
        "agente_cdp": inj_msg,
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    guardar_estado(res)
    return res


def guardar_estado(data: dict) -> None:
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATUS_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Despachador Autónomo de Publicaciones")
    parser.add_argument("--dia", choices=["lunes", "martes", "miercoles", "jueves", "viernes", "sabado", "domingo"], help="Forzar un día de la semana")
    parser.add_argument("--propiedad", help="Forzar una propiedad específica por ID")
    parser.add_argument("--force", action="store_true", help="Ignorar idempotencia y forzar ejecución")
    parser.add_argument("--dry-run", action="store_true", help="Generar y mostrar el plan sin despachar")
    parser.add_argument("--json", action="store_true", help="Salida en formato JSON")
    args = parser.parse_args()

    dia_map = {
        "lunes": 0, "martes": 1, "miercoles": 2, "jueves": 3,
        "viernes": 4, "sabado": 5, "domingo": 6,
    }
    dia_idx = dia_map.get(args.dia) if args.dia else None

    plan = generar_plan_del_dia(dia_idx=dia_idx, propiedad_override=args.propiedad)
    resultado = despachar(plan, force=args.force, dry_run=args.dry_run)

    if args.json:
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    else:
        print(f"[{resultado.get('state')}] {resultado.get('dia', '')} - {resultado.get('fecha', '')}")
        if "detalles" in resultado:
            for d in resultado["detalles"]:
                print(f"  • {d['propiedad']} -> Listas: {d['listas']} | Fotos: {d['fotos']} | Delay: {d['wait']}m")
        if "error" in resultado:
            print(f"  ERROR: {resultado['error']}")
        if "motivo" in resultado:
            print(f"  INFO: {resultado['motivo']}")

    return 0 if resultado.get("state") in ("DONE", "EN_CURSO", "OMITIDO", "DRY_RUN_OK") else 1


if __name__ == "__main__":
    sys.exit(main())
