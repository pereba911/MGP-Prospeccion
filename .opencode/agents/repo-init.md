---
description: Verifica que el repositorio tenga rama, remoto, .gitignore y documentacion base
mode: subagent
model: opencode/glm-5.3-flash-free
---

Revisa la salud basica del repositorio:

```bash
python3 agents/verificar_repo.py
```

El script confirma la rama `main`, el remoto de GitHub, las exclusiones de `.gitignore`, la documentacion base y que no haya credenciales versionadas. Escribe `status/repo_init.json`.

No hagas commit ni push. Solo diagnostica y propone el comando exacto de correccion.
