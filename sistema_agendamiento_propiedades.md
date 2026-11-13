# Sistema de Agendamiento Autónomo de Propiedades para MultiGroup Poster

## 1. Arquitectura Modular Aislada (Cero Confusiones)

Para garantizar que el agente de IA **nunca mezcle las fotos de una propiedad con los textos de otra**, cada inmueble activo opera como un paquete cerrado e independiente dentro de:

[`propiedades/`](propiedades/)

```
propiedades/
├── 01_colinas_san_javier_casa_venta/          Venta - casa
├── 02_country_club_depto_venta/               Venta - departamento
├── 03_elysian_country_amueblado_renta/        Renta - departamento amueblado
├── 04_country_club_200m2_renta/               Renta - departamento
├── 05_torre_opera_depto_renta/                Renta - departamento
├── 06_hyatt_regency_andares_renta/            Renta - departamento
├── 07_torre_hsbc_oficinas_renta/              Renta - oficina
└── 08_americana_estudio_amueblado_renta/      Renta - estudio amueblado
```

Cada carpeta contiene exactamente:

```
<propiedad>/
├── ficha_publicacion.json          Reglas de enrutamiento y listas obligatorias
├── descripciones/                  3 variantes sin emojis + todas_las_variantes.md
├── fotografias/                    Fotos originales exclusivas de la propiedad
└── fotografias_procesadas/         Generado por procesar_fotos.py (no se versiona)
```

Las rutas dentro de cada ficha son **relativas** a la raíz del repositorio (`propiedades/<id>/...`), para que el mismo paquete funcione en la Mac y en la VM.

> **Principio de Aislamiento:** El agente entra exclusivamente a la subcarpeta de la propiedad objetivo. Toma las fotos de su carpeta `fotografias/`, elige una variante de su carpeta `descripciones/` y consulta su `ficha_publicacion.json` para saber con precisión a qué listas de MultiGroup Poster debe publicar.

---

## 2. Matriz de Enrutamiento Estipulada (Routing por Tipo y Ubicación)

Cada archivo `ficha_publicacion.json` ya tiene programado el mapeo estricto hacia las 12 listas de grupos:

| Condición de la Propiedad | Listas de MultiGroup Poster Asignadas por Regla |
| :--- | :--- |
| **Operación: VENTA** | `1. Solo Venta (Inmuebles ZMG)` + Listas de Zona + `12. Inmobiliarios Generales y Asesores ZMG` |
| **Operación: RENTA** | `11. Solo Renta (Departamentos y Casas)` + `2. Venta y Renta (Inmuebles ZMG)` + Listas de Zona + `12. Inmobiliarios Generales y Asesores ZMG` |
| **Tipo: TERRENO** | `3. Terrenos y Lotes (Jalisco / ZMG)` + `12. Inmobiliarios Generales y Asesores ZMG` (+ Lista Venta si aplica) |
| **Tipo: OFICINA en renta** | `4. Oficinas y Corporativos` + `11. Solo Renta` + `2. Venta y Renta` + Lista de Zona + `12. Inmobiliarios Generales y Asesores ZMG` |
| **Tipo: BODEGA** | `5. Bodegas y Naves Industriales` + `12. Inmobiliarios Generales y Asesores ZMG` |
| **Ubicación: Providencia / Country / Monraz** | `7. Zona Providencia - Country Club - Colomos` |
| **Ubicación: Americana / Chapultepec / Lafayette** | `6. Zona Americana - Chapultepec - Lafayette` |
| **Ubicación: Andares / Valle Real / Solares** | `8. Zona Andares - Puerta de Hierro - Valle Real - Solares` |
| **Ubicación: Chapalita / Ciudad del Sol** | `9. Zona Chapalita - Ciudad del Sol` |
| **Ubicación: San Isidro / Cañadas / Centinela** | `10. Zona San Isidro - Cañadas - Centinela` |

La lista 12 se asigna a todas las propiedades activas como bolsa de colaboración entre asesores. Es la única lista que se repite en venta y renta por diseño.

> **Nota sobre la categoría 13:** los 35 grupos `descartados_no_inmobiliarios` de `clasificacion_grupos_facebook.md` son lista negra. Nunca se asignan.

---

## 3. ¿Cómo Manejar la Programación Diaria y Recurrente en MultiGroup Poster?

### El Dilema del Agendamiento Diario vs. Seguridad de Facebook
Facebook sanciona las cuentas que publican exactamente el mismo contenido todos los días en los mismos grupos. Para resolver esto y tener una **presencia diaria continua sin riesgos**, se implementa el **Modelo de Rotación Cruzada**:

| Día | Propiedades | Listas |
| :--- | :--- | :--- |
| **Lunes** | Colinas San Javier, Country Club 128 m2 | Venta (1) + zona + 12 |
| **Martes** | Elysian, Country Club 200 m2, Torre Ópera, Hyatt, HSBC, Americana | Renta (11 + 2) + zona + 12 |
| **Miércoles** | Refuerzo opcional de la propiedad con menos alcance | Lista 12 o zona pendiente |
| **Jueves** | Colinas San Javier, Country Club 128 m2 | Zona + 12 (rotación de variante) |
| **Viernes** | Las seis rentas activas | Zona + 12 (rotación de variante) |
| **Sábado** | Terrenos o bodegas, solo si hay inventario | 3 o 5 + 12 |
| **Domingo** | Descanso algorítmico | Sin publicaciones |

La rotación exacta por propiedad vive en `dias_rotacion_sugeridos` dentro de cada `ficha_publicacion.json`: Lunes y Jueves para venta; Martes y Viernes para renta.

### Reglas de Configuración en la Extensión:
1. **Frecuencia:** Agendar la campaña con repetición semanal en días específicos (ej. Lunes y Jueves para Venta; Martes y Viernes para Renta).
2. **Alternancia de Texto:** Usar una variante diferente cada semana (Variante 1 en semana A, Variante 2 en semana B, Variante 3 en semana C) o usar las plantillas con Spintax de [`agente_instrucciones_publicacion.md`](agente_instrucciones_publicacion.md).
3. **Delays Seguros:** Configurar entre **90 y 180 segundos** entre cada grupo.
4. **Tope Diario:** Máximo **30 a 40 publicaciones al día** en la cuenta.

---

## 4. Ciclo de Vida: Altas Nuevas y Bajas Definitivas

### Cuando entra una NUEVA propiedad a Marketplace:
1. La das de alta normalmente en Facebook Marketplace.
2. Abres Chrome en la Mac con la sesión de Facebook activa y ejecutas el sincronizador:
   ```bash
   python3 actualizar_propiedades_marketplace.py
   ```
   Este paso corre **en la Mac**, no en la VM, porque usa la sesión local de Chrome vía CDP. Actualiza `propiedades_marketplace.json`, `relacion_propiedades_marketplace.md` y el banco de descripciones.
3. Agregas la propiedad al catálogo curado en `organizador_propiedades_autonomo.py` (`CATALOGO_PROPIEDADES`) con sus datos y sus tres variantes sin emojis.
4. Ejecutas:
   ```bash
   python3 organizador_propiedades_autonomo.py
   python3 procesar_fotos.py --datos
   ```
   El organizador crea o refresca `propiedades/<id>/` con `descripciones/`, `fotografias/` y `ficha_publicacion.json`; el pipeline genera `portal_data.json` y los tres lotes.
5. Colocas las fotos en su carpeta `fotografias/`, ejecutas `python3 procesar_fotos.py --todo` y agendes la campaña en MultiGroup Poster.

> El catálogo es deliberadamente curado: el sincronizador no inventa descripciones. Una propiedad nueva no se publica hasta que exista su entrada en `CATALOGO_PROPIEDADES` y su ficha tenga las listas correctas.

### Cuando una propiedad se VENDE o RENTA:
1. La marcas en Marketplace como `Vendida`, `Agotada` o `Alquilada`.
2. Al correr la sincronización quincenal, el sistema actualiza el estado en `relacion_propiedades_marketplace.md`.
3. Retiras manualmente la propiedad de `CATALOGO_PROPIEDADES` y ejecutas `python3 organizador_propiedades_autonomo.py`; la carpeta obsoleta se elimina y deja de republicarse.
4. En MultiGroup Poster, se cancela o pausa la campaña recurrente vinculada a esa propiedad.
