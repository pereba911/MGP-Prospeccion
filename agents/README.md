# Agentes de MGP Prospeccion

Esta carpeta contiene la especificación y las herramientas de los agentes. Las definiciones que OpenCode carga están en `.opencode/agents/`.

## Archivos

| Archivo | Función |
| :--- | :--- |
| `roles.json` | Qué hace cada rol, qué archivos requiere y qué estado debe producir. |
| `modelos_gratuitos.json` | Cadena de 11 modelos con costo 0 y modelo inicial por rol. |
| `cambiar_modelo.py` | Cambia el modelo por defecto y el de cada agente dentro de la cadena gratuita. |
| `verificar_agentes.py` | Revisa definiciones, modelos, archivos, estados, sintaxis y coherencia de fichas. |
| `verificar_repo.py` | Revisa rama, remoto, `.gitignore`, documentación y credenciales versionadas. |

## Cambiar de modelo cuando se agota la cuota

```bash
# Pasa todos los agentes al siguiente modelo gratuito
python3 agents/cambiar_modelo.py --siguiente --motivo "cuota agotada"

# Cambia solo un agente
python3 agents/cambiar_modelo.py --rol content-gen-1 --siguiente

# Fija un modelo concreto de la cadena
python3 agents/cambiar_modelo.py --modelo opencode/glm-5.3-flash-free

# Revisa el modelo actual de cada agente
python3 agents/cambiar_modelo.py --estado
```

El script rechaza modelos que no estén en `modelos_gratuitos.json`, por lo que un cambio de emergencia nunca puede terminar en un modelo de pago.

## Verificar que todos los agentes operen

```bash
python3 agents/verificar_agentes.py
```

El comando revisa:

- definición en `.opencode/agents/<rol>.md`;
- modelo dentro de la cadena gratuita;
- archivos requeridos;
- archivos generados (solo advertencia si aún no existen);
- estado sin errores y con fecha reciente;
- sintaxis de scripts bash y Python;
- que las 8 fichas usen solo las 12 listas operativas y cumplan la regla de operación, tipo y zona;
- que el número de WhatsApp esté configurado.

El resultado se escribe en `status/agentes.json`.

## Roles

| Rol | Responsabilidad |
| :--- | :--- |
| `coordinator` | Orquesta el pipeline y decide el siguiente paso. |
| `repo-init` | Revisa rama, remoto, `.gitignore` y documentación base. |
| `autopush-builder` | Mantiene `autopush.sh` y la sincronización segura con GitHub. |
| `data-collector` | Genera `portal_data.json` y los tres lotes de fotos. |
| `content-gen-1/2/3` | Procesan la iluminación de cada lote con Pillow. |
| `scheduler-validator` | Valida cron, scripts y último push. |
| `alert-bot` | Detecta errores nuevos en el log y registra alertas. |
| `verificador-agentes` | Ejecuta la revisión de salud de todos los roles. |
