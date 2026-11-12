# Guía de Optimización y Carga de Fotografías para MultiGroup Poster

## 1. Estructura de Carpetas Creada en tu Mac

Se ha creado la estructura dentro de este proyecto:
📂 [`/Users/mac/Documents/MGP Prospeccion/fotos_propiedades/`](file:///Users/mac/Documents/MGP%20Prospeccion/fotos_propiedades/)

* `01_colinas_san_javier_venta/` -> Fotos de la residencia en Colinas ($13.8M)
* `02_country_club_128m2_venta/` -> Fotos del depto en Country Club ($10.5M)
* `03_zapopan_venta/` -> Fotos del depto en Zapopan ($1.99M)
* `04_elysian_country_renta/` -> Fotos del depto amueblado resort ($44.9K)

---

## 2. Parámetros Técnicos para Máxima Definición en Facebook

Facebook cuenta con un algoritmo de compresión muy estricto que suele arruinar fotos que se suben en calidades arbitrarias. Para que las fotos se vean **impecables y nítidas**:

1. **Resolución Máxima:** **2048 píxeles en el lado más largo** (por ejemplo: `2048 x 1536 px` en proporción 4:3 o `2048 x 2048 px` en cuadrada 1:1).
   * *¿Por qué 2048 px?* Si subes fotos de 4000 px o tomadas directo de cámara reflex en 20 MB, Facebook las reduce bruscamente y las pixela. Si las escalas previamente a 2048 px, Facebook **las conserva intactas**.
2. **Formato:** **JPG (JPEG)** con compresión del 90-95% o **PNG**.
   * Evitar formatos `.HEIC` (iPhone) o `.WEBP` no estándar para que el motor de la extensión no tenga incompatibilidades.
3. **Espacio de Color:** **sRGB** (garantiza que los colores no se vean lavados o grisáceos en pantallas móviles).
4. **Peso por Archivo:** Entre **1.5 MB y 3.5 MB**.

---

## 3. Orden y Nomenclatura Recomendada (Efecto Collage)

Facebook crea un mosaico visual con las primeras 4 fotos. Nombra tus fotos numéricamente para que se suban en el orden correcto:

* `01_fachada_o_alberca.jpg` (La foto "gancho": vista exterior más impactante o amenidad principal).
* `02_sala_comedor.jpg` (Área social y amplitud).
* `03_cocina.jpg` (Cocina integral y acabados).
* `04_recamara_principal.jpg` (Confort y espacio).
* `05_bano_principal.jpg`
* `06_amenidades_terraza.jpg`
* `07_plano_o_distribucion.jpg` (Opcional).

*Límite óptimo por publicación:* Entre **5 y 8 fotografías** (más de 10 satura al usuario y vuelve lento el proceso de publicación de la extensión).

---

## 4. Métodos para Importar a MultiGroup Poster

### Método A: Manual Rápido (Arrastrar y Soltar)
1. Abre tu carpeta en Finder: `/Users/mac/Documents/MGP Prospeccion/fotos_propiedades/[propiedad]/`.
2. En la pestaña de **MultiGroup Poster** en Chrome, ve al creador de posts.
3. Selecciona las fotos del Finder y arrástralas directamente al recuadro de fotos.
4. Pega la descripción de la propiedad tomada de [`descripciones_vigentes/`](file:///Users/mac/Documents/MGP%20Prospeccion/descripciones_vigentes/).

### Método B: Automatizado vía Agente (Recomendado para el Agente Autónomo)
MultiGroup Poster incluye la herramienta nativa `add_media_from_url`. Si las fotos están alojadas en enlaces públicos HTTPS (por ejemplo, desde EasyBroker CDN, Google Drive público o un hosting web):
1. El agente toma las URLs de las fotos.
2. Llama a `add_media_from_url(url=...)` para descargarlas directo a la extensión en HD.
3. Inyecta los `media_ids` en `create_post` junto con el texto y la lista programada.
