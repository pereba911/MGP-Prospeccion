# Manual Rápido de Ejecución: Máquina de Prospección MGP

Este documento contiene los comandos y accesos exactos para operar el sistema de prospección y publicación.

---

## 1. Dashboard local (tu Mac)

Es la forma recomendada de operar. Corre en tu computadora y controla la VM por SSH.

### Abrir
Haz doble clic en **`dashboard.command`** o, desde la terminal:

```bash
cd "/Users/mac/Documents/MGP Prospeccion"
python3 dashboard_server.py
```

Se abrirá automáticamente en `http://127.0.0.1:8765`.

### Qué muestra
- Estado real de cada proceso: repo, autopush, alert-bot, data-collector, los 3 lotes de fotos, scheduler y Chrome/MultiGroup.
- Si el cron está activo, si hay commits sin subir y si GitHub está bloqueando el push.
- Logs de `autopush` y de alertas.
- Fotos totales y procesadas, espacio en disco y uptime de la VM.

### Botones
| Botón | Qué hace |
| :--- | :--- |
| **Encender automatización** | Instala el cron de autopush (lunes 10:00) y alert-bot (cada 5 min) en la VM. |
| **Detener** | Quita esas dos tareas del cron (no borra archivos ni historial). |
| **Ejecutar autopush ahora** | Corre `autopush.sh` de inmediato y reporta el resultado. |
| **Actualizar inventario** | Ejecuta `actualizar_propiedades_marketplace.py` en la VM. |
| **Regenerar datos y fotos** | Ejecuta `procesar_fotos.py --todo`. |
| **Validar scripts y cron** | Revisa sintaxis de los scripts y confirma las entradas de cron. |
| **Configurar token** | Guarda un nuevo token de GitHub en `.env` (permisos 600). |

### Requisito
La Mac debe poder entrar a la VM sin contraseña:

```bash
ssh root@138.197.15.61 'echo OK'
```

---

## 2. Comando maestro de sincronización (local)

Para actualizar inventario, descripciones y paquetes usando el Chrome local:

```bash
"/Users/mac/Documents/MGP Prospeccion/sincronizar.sh"
```

Hace lo siguiente:
1. Conecta con Facebook vía CDP usando tu sesión de Chrome.
2. Actualiza estados y clics en [`relacion_propiedades_marketplace.md`](relacion_propiedades_marketplace.md).
3. Filtra propiedades vendidas/alquiladas.
4. Regenera las 3 variantes de texto sin emojis en [`descripciones_vigentes/`](descripciones_vigentes/).
5. Mantiene los paquetes de [`propiedades/`](propiedades/) y sus `ficha_publicacion.json`.

> Este comando es manual. La automatización desatendida vive en la VM (ver sección 4).

---

## 3. Pipeline de fotos (sin ImageMagick ni LLM)

```bash
python3 procesar_fotos.py --datos        # portal_data.json + lotes 1-3
python3 procesar_fotos.py --procesar     # mejora iluminación de todas las fotos
python3 procesar_fotos.py --todo         # ambos
python3 procesar_fotos.py --procesar --batch 2 --force
```

- Mejora iluminación, contraste, color y nitidez con Pillow.
- No elimina fondos.
- Solo reduce si la imagen supera **7020 px** en su lado mayor; no inventa resolución en fotos pequeñas.
- Guarda en `propiedades/<id>/fotografias_procesadas/` (los originales no se tocan).
- Escribe `status/content_gen_*.json` y `status/data_collector.json`.

---

## 4. Automatización en la VM (`root@138.197.15.61`)

| Tarea | Comando | Frecuencia |
| :--- | :--- | :--- |
| Autopush | `/home/poster/mgp-prospeccion/autopush.sh` | Lunes 10:00 |
| Alert-Bot | `/home/poster/mgp-prospeccion/alert_bot.sh` | Cada 5 min |

- `autopush.sh` hace `git add`, commit, `pull --rebase` y `push`.
- El token se lee de `.env` (permisos `600`), **nunca** del `crontab` ni del código.
- Al terminar, escribe `status/scheduler_validator.json` con `last_push_ok`.
- `alert_bot.sh` solo revisa las líneas nuevas del log, así no repite alertas viejas.

Para entrar a la VM:

```bash
ssh root@138.197.15.61
```

---

## 5. Dónde consultar la información

| Para ver... | Abre este archivo |
| :--- | :--- |
| **Estado general y control** | `dashboard.command` |
| **Textos listos sin emojis** | [`descripciones_vigentes/descripciones_propiedades_vigentes.md`](descripciones_vigentes/descripciones_propiedades_vigentes.md) |
| **Texto plano (.txt)** | [`descripciones_vigentes/descripciones_propiedades_vigentes.txt`](descripciones_vigentes/descripciones_propiedades_vigentes.txt) |
| **Paquetes y fotos por propiedad** | Carpeta [`propiedades/`](propiedades/) |
| **Estado y clics de Marketplace** | [`relacion_propiedades_marketplace.md`](relacion_propiedades_marketplace.md) |
| **Las 12 listas de grupos** | [`clasificacion_grupos_facebook.md`](clasificacion_grupos_facebook.md) |
| **Reglas del agente de publicación** | [`sistema_agendamiento_propiedades.md`](sistema_agendamiento_propiedades.md) |

---

## 6. Repositorio GitHub

- **URL:** [https://github.com/pereba911/MGP-Prospeccion](https://github.com/pereba911/MGP-Prospeccion)
- **Rama:** `main`
- **Mac:** remoto por SSH (`git@github.com:...`).
- **VM:** remoto HTTPS + token en `.env`.

---

## 7. Problemas comunes

**“GitHub está bloqueando el push” (GH013)**
El historial contiene un token. Se limpió el 2026-11-13; si vuelve a pasar, revisa que `.env` esté ignorado y que ningún script escriba el token en texto plano.

**“Sin conexión con la VM”**
Prueba `ssh root@138.197.15.61 'echo OK'`. Si pide contraseña, falta la clave SSH.

**“Chrome / MultiGroup Poster no está corriendo”**
En la VM: `pgrep -af chrome`. Debe aparecer `--load-extension=/home/poster/multigroup-extension`.

**Token expuesto o revocado**
Rótalo en GitHub → *Settings → Developer settings → Personal access tokens*. Luego guárdalo desde el dashboard con **Configurar token**.
