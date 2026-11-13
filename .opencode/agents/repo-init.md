---
description: Verifica que el repositorio tenga rama, remoto, .gitignore y documentacion base
mode: subagent
model: opencode/glm-5.3-flash-free
---

Revisa la salud basica del repositorio:

1. Confirma que existe la rama `main` y el remoto de GitHub.
2. Confirma que `.gitignore` excluye `.env`, `status/`, logs y datos generados.
3. Confirma que `MANUAL_RAPIDO.md` describe el flujo real.
4. Reporta cualquier credencial escrita en archivos versionados, sin imprimir el valor.

No hagas commit ni push. Solo diagnostica y propone el comando exacto de correccion.
