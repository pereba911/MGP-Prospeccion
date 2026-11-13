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
- Estado local de los 10 agentes y del modelo gratuito que tiene asignado cada uno.
- Si falta el número de WhatsApp en `config_publicacion.json`.
- Si el cron está activo, si hay commits sin subir y si GitHub está bloqueando el push.
- Logs de `autopush` y de alertas.
- Fotos totales y procesadas, espacio en disco y uptime de la VM.

### Botones
| Botón | Dónde corre | Qué hace |
| :--- | :--- | :--- |
| **Encender automatización** | VM | Instala el cron de autopush (lunes 10:00) y alert-bot (cada 5 min). |
| **Detener** | VM | Quita esas dos tareas del cron (no borra archivos ni historial). |
| **Ejecutar autopush ahora** | VM | Corre `autopush.sh` de inmediato y reporta el resultado. |
| **Actualizar inventario** | Mac | Ejecuta `actualizar_propiedades_marketplace.py` con el Chrome local. |
| **Regenerar datos y fotos** | VM | Ejecuta `procesar_fotos.py --todo`. |
| **Validar scripts y cron** | VM | Revisa sintaxis de los scripts y confirma las entradas de cron. |
| **Verificar agentes** | Mac | Ejecuta `agents/verificar_agentes.py`. |
| **Cambiar modelo (cuota)** | Mac | Pasa todos los agentes al siguiente modelo gratuito. |
| **Probar WhatsApp** | VM | Envía un mensaje de prueba con la configuración de `.env`. |
| **Configurar token** | VM | Guarda un nuevo token de GitHub en `.env` (permisos 600). |

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

> Este comando es manual y **debe correr en la Mac**, porque usa la sesión local de Chrome. La automatización desatendida vive en la VM (ver sección 4).

Para una propiedad nueva, el sincronizador no inventa textos: agrega su entrada al catálogo curado `CATALOGO_PROPIEDADES` de `organizador_propiedades_autonomo.py` y ejecuta:

```bash
python3 organizador_propiedades_autonomo.py
python3 procesar_fotos.py --datos
```

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
- Cuando detecta un error, guarda la alerta en `alertas.log` y la envía por **WhatsApp**.

### Alertas por WhatsApp

La configuración vive en `.env` (permisos `600`). Hay dos proveedores:

| Proveedor | Ventaja | Requisitos |
| :--- | :--- | :--- |
| `callmebot` | Gratuito y rápido | `CALLMEBOT_APIKEY` y `WHATSAPP_ALERTAS` |
| `meta` | Oficial de WhatsApp | `META_WA_TOKEN`, `META_WA_PHONE_ID` y `WHATSAPP_ALERTAS` |

Para CallMeBot: envía por WhatsApp el texto `I allow callmebot to send me messages` al **+34 644 51 95 23**. El bot responde con una API key; guárdala en `.env`:

```bash
WHATSAPP_PROVIDER=callmebot
WHATSAPP_ALERTAS=523340088294
CALLMEBOT_APIKEY=tu_api_key
```

Comprueba el envío:

```bash
python3 agents/notificar_whatsapp.py --probar
```

Si aún no hay credenciales, el bot no falla: escribe `whatsapp: sin_configurar` en `status/alert_bot.json`.

Para entrar a la VM:

```bash
ssh root@138.197.15.61
```

---

## 5. Agentes y modelos gratuitos (sin costo adicional)

Los 10 roles viven en `.opencode/agents/` y su especificación en `agents/roles.json`. La cadena de modelos está en `agents/modelos_gratuitos.json`; **todos los modelos de esa cadena tienen costo 0**.

| Rol | Modelo inicial |
| :--- | :--- |
| Coordinador | `opencode/big-pickle` |
| Repo Init | `opencode/glm-5.3-flash-free` |
| Autopush Builder | `opencode/deepseek-v4.1-flash-free` |
| Data Collector | `opencode/minimax-m3.1-flash-free` |
| Content Gen 1 | `opencode/longcat-2.5-free` |
| Content Gen 2 | `opencode/flint-40b-free` |
| Content Gen 3 | `opencode/mimo-v2.6-flash-free` |
| Scheduler Validator | `opencode/inkling-2-small-free` |
| Alert Bot | `opencode/beam-free` |
| Verificador de Agentes | `opencode/nemotron-3.5-super-vl-free` |

### Si se agota la cuota de un modelo

```bash
python3 agents/cambiar_modelo.py --siguiente --motivo "cuota agotada"
```

Eso pasa el modelo por defecto y cada agente al siguiente modelo gratuito de la cadena. También se puede cambiar un solo agente:

```bash
python3 agents/cambiar_modelo.py --rol content-gen-1 --siguiente
```

El script rechaza cualquier modelo que no esté en la cadena gratuita, así que no puede terminar usando un modelo de pago.

### Verificar que todos los agentes operen

```bash
python3 agents/verificar_agentes.py
```

Revisa definición, modelo gratuito, archivos requeridos, estado, antigüedad, sintaxis de scripts y coherencia de las 12 listas con las 8 fichas. Escribe `status/agentes.json` y devuelve código 1 si hay errores.

---

## 6. Dónde consultar la información

| Para ver... | Abre este archivo |
| :--- | :--- |
| **Estado general y control** | `dashboard.command` |
| **Textos listos sin emojis** | [`descripciones_vigentes/descripciones_propiedades_vigentes.md`](descripciones_vigentes/descripciones_propiedades_vigentes.md) |
| **Texto plano (.txt)** | [`descripciones_vigentes/descripciones_propiedades_vigentes.txt`](descripciones_vigentes/descripciones_propiedades_vigentes.txt) |
| **Paquetes y fotos por propiedad** | Carpeta [`propiedades/`](propiedades/) |
| **Estado y clics de Marketplace** | [`relacion_propiedades_marketplace.md`](relacion_propiedades_marketplace.md) |
| **Las 12 listas de grupos** | [`clasificacion_grupos_facebook.md`](clasificacion_grupos_facebook.md) |
| **Reglas del agente de publicación** | [`sistema_agendamiento_propiedades.md`](sistema_agendamiento_propiedades.md) |
| **Roles, modelos y fallback** | [`agents/roles.json`](agents/roles.json) y [`agents/modelos_gratuitos.json`](agents/modelos_gratuitos.json) |
| **Número de WhatsApp** | [`config_publicacion.json`](config_publicacion.json) |

---

## 7. Repositorio GitHub

- **URL:** [https://github.com/pereba911/MGP-Prospeccion](https://github.com/pereba911/MGP-Prospeccion)
- **Rama:** `main`
- **Mac:** remoto por SSH (`git@github.com:...`).
- **VM:** remoto HTTPS + token en `.env`.

---

## 8. Problemas comunes

**“Se agotó la cuota del modelo”**
Ejecuta `python3 agents/cambiar_modelo.py --siguiente --motivo "cuota agotada"`. Todos los modelos de la cadena son gratuitos; no hay costo adicional.

**“Hay fallos en agentes o modelos locales”**
Ejecuta `python3 agents/verificar_agentes.py` y corrige lo que marque en rojo. El detalle queda en `status/agentes.json`.

**“Falta el número de WhatsApp”**
Escribe el número internacional (sin `+` ni espacios) en `whatsapp_numero` dentro de `config_publicacion.json`, por ejemplo `523312345678`. Después ejecuta `python3 organizador_propiedades_autonomo.py` para regenerar las fichas.

**“GitHub está bloqueando el push” (GH013)**
El historial contiene un token. Se limpió el 2026-11-13; si vuelve a pasar, revisa que `.env` esté ignorado y que ningún script escriba el token en texto plano.

**“Sin conexión con la VM”**
Prueba `ssh root@138.197.15.61 'echo OK'`. Si pide contraseña, falta la clave SSH.

**“Chrome / MultiGroup Poster no está corriendo”**
En la VM: `pgrep -af chrome`. Debe aparecer `--load-extension=/home/poster/multigroup-extension`.

**Token expuesto o revocado**
Rótalo en GitHub → *Settings → Developer settings → Personal access tokens*. Luego guárdalo desde el dashboard con **Configurar token**.
