# Manual Rápido de Ejecución: Máquina de Prospección MGP

Este documento contiene los **comandos exactos de terminal (Bash)** que puedes copiar y pegar para correr el sistema de forma semiautomatizada.

---

## 1. El Comando Maestro (Sincronización Total)

Para actualizar todo el proyecto cada dos semanas (o cada vez que agregues/vendas una propiedad en Marketplace), abre tu Terminal y ejecuta:

```bash
/Users/mac/Documents/MGP\ Prospeccion/sincronizar.sh
```

*(O si ya estás dentro de la carpeta del proyecto: `./sincronizar.sh`)*

### ¿Qué ejecuta este único comando en segundo plano?
1. **Conecta con Facebook:** Consulta silenciosamente tu sesión activa de Chrome vía CDP (sin abrir ventanas ni robar el foco).
2. **Actualiza el Inventario de Marketplace:** Registra clics, estados (`Disponible`, `Agotado`, `Vendido`, `Alquilado`) en [`relacion_propiedades_marketplace.md`](file:///Users/mac/Documents/MGP%20Prospeccion/relacion_propiedades_marketplace.md).
3. **Filtra Propiedades Activas:** Descarta las vendidas/alquiladas y deja solo las vigentes a republicar.
4. **Regenera Descripciones sin Emojis:** Actualiza las 3 variantes de texto profesionales por propiedad en [`descripciones_vigentes/`](file:///Users/mac/Documents/MGP%20Prospeccion/descripciones_vigentes/).
5. **Actualiza los Paquetes Modulares:** Revisa las carpetas en [`propiedades/`](file:///Users/mac/Documents/MGP%20Prospeccion/propiedades/), crea las de propiedades nuevas con sus subcarpetas de fotos/textos y actualiza su archivo `ficha_publicacion.json` con las listas de grupos correspondientes.

---

## 2. Dónde Consultar la Información en 1 Clic

| Para ver... | Abre este archivo |
| :--- | :--- |
| **Copiar textos listos sin emojis (1 clic)** | [`descripciones_vigentes/descripciones_propiedades_vigentes.md`](file:///Users/mac/Documents/MGP%20Prospeccion/descripciones_vigentes/descripciones_propiedades_vigentes.md) |
| **Copiar textos en texto plano (.txt)** | [`descripciones_vigentes/descripciones_propiedades_vigentes.txt`](file:///Users/mac/Documents/MGP%20Prospeccion/descripciones_vigentes/descripciones_propiedades_vigentes.txt) |
| **Ver paquetes y fotos por propiedad** | Carpeta [`propiedades/`](file:///Users/mac/Documents/MGP%20Prospeccion/propiedades/) |
| **Ver estado y clics de Marketplace** | [`relacion_propiedades_marketplace.md`](file:///Users/mac/Documents/MGP%20Prospeccion/relacion_propiedades_marketplace.md) |
| **Ver las 12 listas de grupos clasificadas** | [`clasificacion_grupos_facebook.md`](file:///Users/mac/Documents/MGP%20Prospeccion/clasificacion_grupos_facebook.md) |
| **Ver las reglas del agente de publicación** | [`sistema_agendamiento_propiedades.md`](file:///Users/mac/Documents/MGP%20Prospeccion/sistema_agendamiento_propiedades.md) |

---

## 3. Automatización Total con Cron (Cada Lunes a las 9:00 AM)

Para que tu Mac ejecute la sincronización automáticamente todos los lunes sin que tengas que abrir la terminal, agregamos esta línea a tu `crontab`:

```bash
0 9 * * 1 /Users/mac/Documents/MGP\ Prospeccion/sincronizar.sh >> /Users/mac/Documents/MGP\ Prospeccion/sync.log 2>&1
```

### ¿Qué hace la rutina autónoma de los lunes?
1. Detecta si hay propiedades nuevas en Marketplace o cambios de estado.
2. Regenera las variantes de texto profesionales sin emojis en `descripciones_vigentes/`.
3. Actualiza y limpia las carpetas en `propiedades/`.
4. **Auto-commit & push a GitHub:** Sube automáticamente los cambios al repositorio remoto en [https://github.com/pereba911/MGP-Prospeccion](https://github.com/pereba911/MGP-Prospeccion).

---

## 4. Repositorio GitHub y Sincronización Remota

- **URL Oficial del Repositorio:** [https://github.com/pereba911/MGP-Prospeccion](https://github.com/pereba911/MGP-Prospeccion)
- **Rama Principal:** `main`
- **Autenticación:** SSH segura vinculada a tu cuenta `pereba911`.
- **Régimen de respaldo:** Cada vez que corre `sincronizar.sh` (manual o por cron), si detecta cambios realiza `git commit` y `git push` de forma desatendida.

