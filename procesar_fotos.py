#!/usr/bin/env python3
"""Pipeline deterministico de fotos y datos para MGP Prospeccion.

No depende de agentes/LLM ni de ImageMagick: usa Pillow.

Uso:
    python3 procesar_fotos.py --datos              # portal_data.json + batches
    python3 procesar_fotos.py --procesar           # mejora iluminacion de todas
    python3 procesar_fotos.py --procesar --batch 1 # solo un batch
    python3 procesar_fotos.py --todo               # datos + procesar

Salidas:
    portal_data.json
    fotos_batch/batch-{1,2,3}/lista.txt
    propiedades/<id>/fotografias_procesadas/
    status/data_collector.json
    status/content_gen_{1,2,3}.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent
PROPIEDADES = BASE / "propiedades"
BATCH_DIR = BASE / "fotos_batch"
STATUS_DIR = BASE / "status"
EXT_IMAGEN = {".jpg", ".jpeg", ".png", ".webp"}
MAX_DIM = 7020
N_BATCHES = 3


def ahora() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")


def escribir_json(ruta: Path, datos: dict) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def cargar_ficha(carpeta: Path) -> dict:
    ficha = carpeta / "ficha_publicacion.json"
    if not ficha.exists():
        return {}
    try:
        return json.loads(ficha.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def leer_descripciones(carpeta: Path) -> dict:
    desc_dir = carpeta / "descripciones"
    salida: dict[str, str] = {}
    patrones = {
        "variante_1": "variante_1_*.txt",
        "variante_2": "variante_2_*.txt",
        "variante_3": "variante_3_*.txt",
    }
    for clave, patron in patrones.items():
        archivos = sorted(desc_dir.glob(patron)) if desc_dir.exists() else []
        salida[clave] = archivos[0].read_text(encoding="utf-8").strip() if archivos else ""
    return salida


def listar_fotos(carpeta: Path) -> list[Path]:
    fotos_dir = carpeta / "fotografias"
    if not fotos_dir.exists():
        return []
    fotos = [
        p for p in sorted(fotos_dir.iterdir())
        if p.is_file() and p.suffix.lower() in EXT_IMAGEN
    ]
    return fotos


def recolectar() -> list[dict]:
    propiedades = []
    for carpeta in sorted(p for p in PROPIEDADES.iterdir() if p.is_dir()):
        ficha = cargar_ficha(carpeta)
        fotos = listar_fotos(carpeta)
        if not ficha and not fotos:
            continue
        propiedades.append({
            "id": carpeta.name,
            "propiedad_id": ficha.get("propiedad_id", carpeta.name),
            "nombre": ficha.get("nombre_oficial", carpeta.name),
            "operacion": ficha.get("operacion", ""),
            "tipo_inmueble": ficha.get("tipo_inmueble", ""),
            "precio": ficha.get("precio", ""),
            "ubicacion": ficha.get("ubicacion", ""),
            "estado": ficha.get("estado", ""),
            "fotos": [str(p.relative_to(BASE)) for p in fotos],
            "descripciones": leer_descripciones(carpeta),
            "_carpeta": carpeta,
            "_fotos_abs": fotos,
        })
    return propiedades


def construir_datos() -> None:
    propiedades = recolectar()
    total_fotos = sum(len(p["_fotos_abs"]) for p in propiedades)

    # Reparto equilibrado de fotos en N batches (round-robin por propiedad).
    batches: list[list[str]] = [[] for _ in range(N_BATCHES)]
    indice = 0
    for prop in propiedades:
        for foto in prop["_fotos_abs"]:
            batches[indice % N_BATCHES].append(str(foto.relative_to(BASE)))
            indice += 1

    BATCH_DIR.mkdir(parents=True, exist_ok=True)
    for n, lista in enumerate(batches, start=1):
        destino = BATCH_DIR / f"batch-{n}"
        destino.mkdir(parents=True, exist_ok=True)
        (destino / "lista.txt").write_text("\n".join(lista) + ("\n" if lista else ""), encoding="utf-8")

    portal = {
        "generado": ahora(),
        "total_propiedades": len(propiedades),
        "total_fotos": total_fotos,
        "propiedades": [
            {k: v for k, v in p.items() if not k.startswith("_")} for p in propiedades
        ],
    }
    escribir_json(BASE / "portal_data.json", portal)
    escribir_json(STATUS_DIR / "data_collector.json", {
        "state": "DONE",
        "propiedades": len(propiedades),
        "fotos": total_fotos,
        "batches": N_BATCHES,
        "updated": ahora(),
    })

    print(f"portal_data.json: {len(propiedades)} propiedades, {total_fotos} fotos")
    for n, lista in enumerate(batches, start=1):
        print(f"  batch-{n}: {len(lista)} fotos")


def mejorar_foto(origen: Path, destino: Path) -> tuple[int, int]:
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    Image.MAX_IMAGE_PIXELS = None
    with Image.open(origen) as img:
        img = ImageOps.exif_transpose(img)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Iluminacion profesional de estudio inmobiliario (sin quitar fondos).
        img = ImageOps.autocontrast(img, cutoff=2)
        img = ImageEnhance.Brightness(img).enhance(1.06)
        img = ImageEnhance.Contrast(img).enhance(1.12)
        img = ImageEnhance.Color(img).enhance(1.04)
        img = img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=80, threshold=3))

        ancho, alto = img.size
        mayor = max(ancho, alto)
        if mayor > MAX_DIM:
            factor = MAX_DIM / mayor
            img = img.resize((round(ancho * factor), round(alto * factor)), Image.LANCZOS)
            ancho, alto = img.size

        destino.parent.mkdir(parents=True, exist_ok=True)
        if destino.suffix.lower() in {".jpg", ".jpeg"}:
            img.save(destino, "JPEG", quality=92, optimize=True, subsampling=0)
        else:
            img.save(destino, optimize=True)
        return ancho, alto


def procesar(batch: int | None = None, force: bool = False) -> None:
    pendientes: list[str] = []
    if batch is not None:
        lista = BATCH_DIR / f"batch-{batch}" / "lista.txt"
        if not lista.exists():
            raise SystemExit(f"No existe {lista}. Ejecuta primero --datos.")
        pendientes = [linea for linea in lista.read_text(encoding="utf-8").splitlines() if linea.strip()]
    else:
        for prop in recolectar():
            pendientes.extend(str(p.relative_to(BASE)) for p in prop["_fotos_abs"])

    total = len(pendientes)
    procesadas = 0
    errores = 0
    print(f"Procesando {total} fotos...")
    for i, rel in enumerate(pendientes, start=1):
        origen = BASE / rel
        carpeta = origen.parent.parent  # .../fotografias -> .../<propiedad>
        destino = carpeta / "fotografias_procesadas" / origen.name
        if destino.exists() and not force:
            procesadas += 1
            continue
        try:
            ancho, alto = mejorar_foto(origen, destino)
            procesadas += 1
            print(f"  [{i}/{total}] OK {origen.name} -> {ancho}x{alto}")
        except Exception as exc:  # noqa: BLE001
            errores += 1
            print(f"  [{i}/{total}] ERROR {origen.name}: {exc}", file=sys.stderr)

    estado = "DONE" if errores == 0 else "ERROR"
    if batch is not None:
        escribir_json(STATUS_DIR / f"content_gen_{batch}.json", {
            "state": estado,
            "batch": batch,
            "procesadas": procesadas,
            "total": total,
            "errores": errores,
            "updated": ahora(),
        })
    else:
        for n in range(1, N_BATCHES + 1):
            lista = BATCH_DIR / f"batch-{n}" / "lista.txt"
            cantidad = len([l for l in lista.read_text(encoding="utf-8").splitlines() if l.strip()]) if lista.exists() else 0
            escribir_json(STATUS_DIR / f"content_gen_{n}.json", {
                "state": estado,
                "batch": n,
                "procesadas": cantidad,
                "total": cantidad,
                "errores": errores,
                "updated": ahora(),
            })

    print(f"Listo: {procesadas} procesadas, {errores} errores")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline de fotos MGP Prospeccion")
    parser.add_argument("--datos", action="store_true", help="genera portal_data.json y batches")
    parser.add_argument("--procesar", action="store_true", help="mejora iluminacion de fotos")
    parser.add_argument("--todo", action="store_true", help="datos + procesar")
    parser.add_argument("--batch", type=int, choices=range(1, N_BATCHES + 1), help="procesar un batch")
    parser.add_argument("--force", action="store_true", help="reprocesar fotos ya existentes")
    args = parser.parse_args()

    if not (args.datos or args.procesar or args.todo):
        args.todo = True

    if args.todo or args.datos:
        construir_datos()
    if args.todo or args.procesar:
        procesar(batch=args.batch, force=args.force)


if __name__ == "__main__":
    main()
