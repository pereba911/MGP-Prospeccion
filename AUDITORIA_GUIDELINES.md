# Auditoría de Guidelines vs. Estado Real del Proyecto

**Fecha:** 2026-11-13
**Alcance:** `agente_instrucciones_publicacion.md`, `sistema_agendamiento_propiedades.md`, `clasificacion_grupos_facebook.md`, `MANUAL_RAPIDO.md`, fichas de propiedad, scripts de automatización y configuración de agentes.

## Resumen

Las guidelines describían un sistema más automatizado de lo que el repositorio realmente hacía. Se corrigieron las incoherencias documentales y los defectos operativos que impedían que los agentes funcionaran igual en la Mac y en la VM. La verificación automática queda en `agents/verificar_agentes.py`.

## Hallazgos y correcciones

| # | Hallazgo | Riesgo | Corrección |
| :---: | :--- | :--- | :--- |
| 1 | El árbol de `propiedades/` mostraba 4 carpetas e incluía `03_zapopan_depto_venta`, que no existe. | El agente buscaba propiedades inexistentes. | Árbol actualizado a las 8 carpetas reales. |
| 2 | La tabla de enrutamiento decía Renta = listas 11 + 2 + zona, pero las fichas reales también asignan la lista 12. | Reglas contradictorias entre documento y fichas. | Tabla y diagrama actualizados: la lista 12 aplica a todas las propiedades activas. |
| 3 | Las fichas de oficina en renta incluyen listas de renta (11 y 2) que la tabla no contemplaba. | El agente podía “corregir” una ficha correcta. | Regla específica para oficina en renta documentada. |
| 4 | Las fichas guardaban rutas absolutas `/Users/mac/...`. | En la VM esas rutas no existen. | Rutas convertidas a relativas (`propiedades/<id>/...`). |
| 5 | Los 8 comentarios de WhatsApp tenían `52XXXXXXXXXX`. | Se publicaría un enlace roto. | Número centralizado en `config_publicacion.json`; si falta, el verificador lo reporta y no debe publicarse. |
| 6 | La plantilla de publicación incluía emojis, aunque el estándar de producción es sin emojis. | Textos inconsistentes con la preferencia del proyecto. | Plantilla reescrita sin emojis y con acentos correctos. |
| 7 | El diagrama de enrutamiento mencionaba “Red Inmobiliaria ZMG”, que no es una lista real. | Nombre inexistente en MultiGroup Poster. | Reemplazado por “12. Inmobiliarios Generales y Asesores ZMG”. |
| 8 | `content_generator.sh` estaba corrupto (variables vacías y comandos inexistentes). | El pipeline de fotos no corría. | Reemplazado por un wrapper de `procesar_fotos.py` con Pillow. |
| 9 | `organizador_propiedades_autonomo.py` y `actualizar_propiedades_marketplace.py` tenían rutas absolutas de la Mac. | Fallaban al ejecutarse en la VM. | Rutas calculadas desde la ubicación del script. |
| 10 | La documentación prometía detección automática de propiedades nuevas, pero el organizador usa un catálogo curado. | Expectativa falsa y propiedades sin ficha. | Documentado el flujo real: actualizar `CATALOGO_PROPIEDADES` y ejecutar el organizador. |
| 11 | El dashboard ejecutaba “Actualizar inventario” en la VM, pero ese script necesita el Chrome de la Mac. | El botón siempre fallaba. | Esa acción ahora corre localmente en la Mac. |
| 12 | La lista 12 se llamaba “Red Inmobiliaria / Asesores” en la clasificación y “Inmobiliarios Generales y Asesores ZMG” en el JSON. | Nombres distintos para la misma lista. | Nombre unificado. |
| 13 | La categoría 13 (35 descartados) podía confundirse con una lista operativa. | Riesgo de publicar en grupos no inmobiliarios. | Aclarado que es lista negra y que las listas operativas son 12. |
| 14 | No existía fallback de modelos ni verificación de agentes. | Un agente quedaba detenido al agotarse la cuota. | 10 agentes definidos, cadena de 11 modelos gratuitos y conmutador automático. |

## Verificación de coherencia

- **12 listas operativas** con los conteos del JSON: 58, 44, 28, 9, 18, 8, 14, 15, 7, 6, 41 y 76.
- **324 asignaciones** en total, **219 grupos únicos** (254 analizados menos 35 descartados). La diferencia se explica porque un grupo puede estar en una lista temática y en una de zona.
- **35 grupos en lista negra** y **0 grupos de la lista negra** dentro de las 12 listas operativas.
- **8 fichas de propiedad**; todas usan listas existentes y cumplen la regla de operación, tipo y zona.
- **13 publicaciones de Marketplace** verificadas: 4 venta, 6 renta y 3 artículos no inmobiliarios.
- **10 roles de agente**, cada uno con definición, modelo gratuito y archivos verificables.
- **11 modelos disponibles**, todos con costo 0.

## Cómo verificar

```bash
python3 agents/verificar_agentes.py
python3 agents/cambiar_modelo.py --estado
```

## Pendientes que requieren decisión o dato del usuario

1. **Número de WhatsApp:** escribir el número internacional en `config_publicacion.json` y regenerar fichas.
2. **Rotación del token de GitHub:** el token anterior estuvo expuesto en logs; debe rotarse desde GitHub y guardarse con el dashboard.
3. **Alertas por WhatsApp:** implementadas con `agents/notificar_whatsapp.py` (CallMeBot o Meta Cloud API). Falta cargar la API key de CallMeBot o las credenciales de Meta en `.env`.
4. **Programación automática en MultiGroup Poster:** sigue pendiente la selección de días, hora y confirmación dentro de la extensión.
