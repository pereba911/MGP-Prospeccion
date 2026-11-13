#!/usr/bin/env python3
"""
organizador_propiedades_autonomo.py
Crea y mantiene paquetes modulares aislados ÚNICAMENTE para las propiedades ACTIVAS seleccionadas:
  /propiedades/<id_propiedad>/
    ├── descripciones/ (3 variantes limpias sin emojis)
    ├── fotografias/   (archivos ordenados 01_fachada.jpg, etc.)
    └── ficha_publicacion.json (reglas estrictas de enrutamiento a MultiGroup Poster)

REGLA DE DEPURACIÓN AUTOMÁTICA:
  Cualquier carpeta en /propiedades/ que ya NO corresponda a una propiedad activa
  es ELIMINADA automáticamente para mantener el proyecto 100% limpio y fiel a Marketplace.
"""

import json
import os
import re
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROPIEDADES_DIR = os.path.join(BASE_DIR, 'propiedades')
MARKETPLACE_JSON = os.path.join(BASE_DIR, 'propiedades_marketplace.json')
LISTAS_MGP_JSON = os.path.join(BASE_DIR, 'listas_para_multigroup_poster.json')
CONFIG_PUBLICACION = os.path.join(BASE_DIR, 'config_publicacion.json')


def whatsapp_url():
    """Devuelve la URL de WhatsApp configurada o un marcador visible si falta."""
    numero = ''
    try:
        with open(CONFIG_PUBLICACION, encoding='utf-8') as fh:
            numero = str(json.load(fh).get('whatsapp_numero', '')).strip()
    except Exception:
        numero = ''
    numero = re.sub(r'\D', '', numero)
    return 'https://wa.me/%s' % numero if numero else 'https://wa.me/{WHATSAPP_NUMERO}'

def clean_no_emojis(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FA6F"
        "\U0001FA70-\U0001FAFF"
        "\U00002600-\U000026FF"
        "\U00002B50"
        "\U00002728"
        "]+", flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    return re.sub(r' +', ' ', text).strip()

def determine_routing_lists(tipo_inmueble, operacion, ubicacion):
    listas = []
    
    # 1. Tipo Especializado
    if tipo_inmueble == 'terreno':
        listas.append("3. Terrenos y Lotes (Jalisco / ZMG)")
    elif tipo_inmueble == 'oficina':
        listas.append("4. Oficinas y Corporativos")
    elif tipo_inmueble in ['bodega', 'nave industrial']:
        listas.append("5. Bodegas y Naves Industriales")
        
    # 2. Operación Comercial
    if operacion.lower() == 'venta':
        listas.append("1. Solo Venta (Inmuebles ZMG)")
    elif operacion.lower() == 'renta':
        listas.append("11. Solo Renta (Departamentos y Casas)")
        listas.append("2. Venta y Renta (Inmuebles ZMG)")
        
    # 3. Zona / Colonia
    ub_lower = ubicacion.lower()
    if any(z in ub_lower for z in ['providencia', 'country', 'monraz', 'colomos', 'san javier', 'torre hsbc']):
        listas.append("7. Zona Providencia - Country Club - Colomos")
        
    if any(z in ub_lower for z in ['americana', 'chapultepec', 'lafayette', 'moderna']):
        listas.append("6. Zona Americana - Chapultepec - Lafayette")
        
    if any(z in ub_lower for z in ['andares', 'puerta de hierro', 'valle real', 'solares', 'jardin real', 'virreyes', 'opera', 'hyatt']):
        listas.append("8. Zona Andares - Puerta de Hierro - Valle Real - Solares")
        
    if any(z in ub_lower for z in ['chapalita', 'ciudad del sol', 'tepeyac', 'la calma']):
        listas.append("9. Zona Chapalita - Ciudad del Sol")
        
    # 4. Red General de Asesores
    listas.append("12. Inmobiliarios Generales y Asesores ZMG")
    
    seen = set()
    dedup = []
    for l in listas:
        if l not in seen:
            seen.add(l)
            dedup.append(l)
    return dedup

# CATÁLOGO DE PROPIEDADES CONFIRMADAS ACTIVAS (8 PROPIEDADES CONSECUTIVAS)
CATALOGO_PROPIEDADES = [
    {
        'folder_name': '01_colinas_san_javier_casa_venta',
        'id': 'COLINAS-SAN-JAVIER-VTA',
        'nombre_oficial': 'Residencia en Colinas de San Javier',
        'tipo_inmueble': 'casa',
        'operacion': 'Venta',
        'precio_formato': '$13,800,000 MXN',
        'ubicacion': 'Colinas de San Javier, Guadalajara / Zapopan',
        'superficie': '273 m2 construccion',
        'recamaras': 3,
        'banos': 4,
        'cocheras': 2,
        'descripcion_corta': 'Residencia de 273 m2 en Colinas de San Javier con 3 habitaciones, 4 banos completos y acabados de lujo.',
        'descripciones': {
            'variante_1_ejecutiva': clean_no_emojis("""OPORTUNIDAD DE VENTA EN COLINAS DE SAN JAVIER

Residencia disponible en una de las zonas residenciales de mayor prestigio y plusvalia de la Zona Metropolitana de Guadalajara.

Ficha Tecnica:
- Superficie construida: 273 m2.
- Distribucion: 3 amplias habitaciones con bano completo y vestidor.
- 4 banos completos en total.
- Sala y comedor independientes con iluminacion natural.
- Cocina integral con barra de granito y alacena de gran capacidad.
- Cochera privada techada.
- Area de lavado y cuarto de servicio independiente.

Precio de venta: $13,800,000 MXN.
Estatus legal: Documentacion en regla, lista para escrituracion inmediata. Aceptamos creditos hipotecarios bancarios y recursos propios.

Para informacion detallada o coordinar un recorrido presencial, favor de comunicarse directamente por mensaje o llamada."""),
            'variante_2_estilo_vida': clean_no_emojis("""EXCLUSIVA RESIDENCIA EN COLINAS DE SAN JAVIER

Vive en el entorno mas tranquilo, arbolado y seguro de Guadalajara. Esta propiedad combina amplitud arquitectonica, privacidad absoluta y una ubicacion inmejorable cerca de los mejores colegios, centros comerciales y zonas corporativas de Puerta de Hierro y Providencia.

Espacios interiores:
- 3 recamaras principales disenadas para maximo confort, cada una con bano completo.
- Sala familiar y estancia con techos de generosa altura.
- Cocina moderna pensada para convivencia familiar.
- 273 m2 disenados para disfrutar de cada rincon sin saturacion.

Inversion: $13,800,000 MXN. Trato profesional y seguro.
Agenda una cita previa para conocer la residencia."""),
            'variante_3_inversion': clean_no_emojis("""PRECIO ESPECIAL POR METRO CUADRADO EN COLINAS DE SAN JAVIER

Si buscas proteger tu patrimonio en una zona consolidada donde el valor por metro cuadrado se incrementa ano con ano, esta es la propiedad adecuada.

Puntos clave:
- Ubicacion privilegiada en Colinas de San Javier con accesos agiles por avenidas principales.
- 273 metros cuadrados de construccion solida con 3 habitaciones y 4 banos.
- Excelente estado de conservacion, lista para ser habitada de inmediato.
- Alta plusvalia garantizada para reventa o inversion patrimonial.

Precio de oportunidad: $13,800,000 MXN.
Se muestra con previa confirmacion. Contacto directo para atender solicitudes de inversionistas y compradores particulares.""")
        }
    },
    {
        'folder_name': '02_country_club_depto_venta',
        'id': 'COUNTRY-CLUB-128-VTA',
        'nombre_oficial': 'Departamento de Lujo en Country Club Guadalajara',
        'tipo_inmueble': 'departamento',
        'operacion': 'Venta',
        'precio_formato': '$10,500,000 MXN',
        'ubicacion': 'Country Club, Guadalajara',
        'superficie': '128 m2 habitables',
        'recamaras': 3,
        'banos': 4,
        'cocheras': 2,
        'descripcion_corta': 'Departamento de 128 m2 en Country Club con 3 habitaciones con bano privado, 4 banos completos y acabados de lujo.',
        'descripciones': {
            'variante_1_ejecutiva': clean_no_emojis("""DEPARTAMENTO EN VENTA EN COUNTRY CLUB GUADALAJARA

Excelente unidad disponible en el tradicional y cotizado cuadrante del Country Club. Diseno moderno, espacios funcionales y acabados de primera linea.

Caracteristicas:
- Area habitable: 128 m2.
- 3 habitaciones con bano privado y closets de carpinteria fina.
- 4 banos completos en total.
- Sala y comedor con ventanales de piso a techo y vista panoramica.
- Cocina integral con barra desayunadora y cubierta de piedra natural.
- 2 cajones de estacionamiento en sotano.
- Torre con caseta de vigilancia 24/7 y acceso controlado.

Precio de venta: $10,500,000 MXN.
Propiedad lista para escriturar. Se aceptan y gestionan creditos hipotecarios.
Contactame para recibir la ficha tecnica y coordinar una visita."""),
            'variante_2_estilo_vida': clean_no_emojis("""VIVE EN EL CORAZON DE COUNTRY CLUB GUADALAJARA

Ubicado a escasos minutos de Providencia, zona financiera y los mejores restaurantes de la ciudad, este departamento de 128 m2 ofrece el balance perfecto entre confort, conectividad y exclusividad.

Distribucion:
- 3 comodas recamaras con bano propio, pensadas para la comodidad de toda la familia.
- Area social amplia e integrada a la cocina de concepto abierto.
- Instalaciones impecables y amenidades privadas dentro del complejo.
- 4 banos completos para maxima practicidad.

Precio: $10,500,000 MXN.
Solicita una presentacion privada y conoce este espacio disenado para tu estilo de vida."""),
            'variante_3_inversion': clean_no_emojis("""OPORTUNIDAD DE INVERSION PATRIMONIAL EN COUNTRY CLUB

Adquiere un departamento en una de las colonias con mayor demanda de vivienda ejecutiva en Guadalajara. Con 128 m2, 3 recamaras y 4 banos, este departamento garantiza alta demanda de renta y solida apreciacion de capital.

Aspectos destacados:
- Ubicacion de gran demanda para ejecutivos, medicos y empresarios.
- Costo por metro cuadrado altamente competitivo en la zona Country Club.
- Edificio consolidado con estricto filtro de seguridad y mantenimiento continuo.

Valor: $10,500,000 MXN.
Para mayores informes y atencion personalizada, comunicate via mensaje directo o llamada.""")
        }
    },
    {
        'folder_name': '03_elysian_country_amueblado_renta',
        'id': 'ELYSIAN-COUNTRY-RNT',
        'nombre_oficial': 'Departamento Amueblado Resort Elysian High Country',
        'tipo_inmueble': 'departamento',
        'operacion': 'Renta',
        'precio_formato': '$44,900 MXN / mes',
        'ubicacion': 'Elysian High Country, Country Club, Guadalajara',
        'superficie': '104.9 m2 habitables',
        'recamaras': 3,
        'banos': 3,
        'cocheras': 2,
        'descripcion_corta': 'Departamento de 104.9 m2 amueblado de lujo en Country Club con 3 recamaras, 3 banos completos, 2 estacionamientos y amenidades resort.',
        'descripciones': {
            'variante_1_ejecutiva': clean_no_emojis("""DEPARTAMENTO AMUEBLADO EN RENTA EN ELYSIAN HIGH COUNTRY

Disenado para quienes buscan un estilo de vida activo, social y exclusivo. Disfruta de instalaciones deportivas de primer nivel y convivencia premium sin salir de tu edificio.

Distribucion y espacios (104.9 m2 | Totalmente Amueblado):
- 3 recamaras amuebladas con estilo moderno (espacio para habitacion principal, visitas o area fitness/estudio).
- 3 banos completos de diseno contemporaneo.
- Sala y comedor de concepto abierto para recibir invitados con estilo.
- Cocina integral moderna y equipada con barra desayunadora.
- 2 cajones de estacionamiento exclusivos.
- Estatus: Listo para habitar inmediatamente.

Condiciones de renta:
- Renta mensual: $44,900 MXN (Incluye cuota de mantenimiento y acceso a todas las amenidades del desarrollo).
- Amenidades estilo resort: Canchas deportivas (padel y tenis), alberca, gimnasio equipado, areas sociales y seguridad 24/7.

Requisitos basicos de arrendamiento y contrato con poliza juridica. Contactanos para agendar un recorrido presencial."""),
            'variante_2_estilo_vida': clean_no_emojis("""RESIDENCIA EJECUTIVA EN RENTA EN COUNTRY CLUB: ELYSIAN

Departamento totalmente amueblado y decorado con estandar ejecutivo, ideal para expatriados, directivos o profesionales que requieren una solucion llave en mano en Guadalajara.

Aspectos principales:
- Ubicado en Torre Elysian High Country, una de las zonas mas exclusivas y seguras de la ciudad.
- 3 habitaciones confortables totalmente amobladas con camas, closets y decoracion selecta.
- 3 banos completos.
- Cocina equipada con electrodomesticos de linea premium.
- Vista panoramica y balcon privado.

Renta: $44,900 MXN mensuales con mantenimiento incluido.
Comunicate hoy mismo para conocer los terminos y programar tu cita."""),
            'variante_3_inversion': clean_no_emojis("""OPORTUNIDAD DE RENTA EN COUNTRY CLUB: 3 HABITACIONES AMUEBLADO

Renta departamento totalmente listo para ocupar en Country Club. Ubicacion estrategica para quienes laboran en Zona Financiera Punto Sao Paulo, Providencia o Chapultepec.

Equipamiento completo:
- 104.9 metros cuadrados aprovechados al maximo.
- 3 recamaras, 3 banos completos, sala de TV, comedor y cocina con cubierta de cuarzo.
- Seguridad en accesos las 24 horas y estacionamiento techado para 2 autos.
- Complejo con amenidades completas de primer orden.

Canon de arrendamiento: $44,900 MXN mensuales.
Atencion personalizada y trato profesional directo. Escribenos para programar una visita.""")
        }
    },
    {
        'folder_name': '04_country_club_200m2_renta',
        'id': 'COUNTRY-CLUB-200-RNT',
        'nombre_oficial': 'Amplio Departamento 200 m2 en Country Club',
        'tipo_inmueble': 'departamento',
        'operacion': 'Renta',
        'precio_formato': '$40,000 MXN / mes',
        'ubicacion': 'Country Club, Guadalajara',
        'superficie': '200 m2 habitables',
        'recamaras': 3,
        'banos': 3.5,
        'cocheras': 2,
        'descripcion_corta': 'Gran departamento de 200 m2 en la mejor zona de Country Club con 3 habitaciones, 3.5 banos y excelentes vistas.',
        'descripciones': {
            'variante_1_ejecutiva': clean_no_emojis("""AMPLIO DEPARTAMENTO EN RENTA EN COUNTRY CLUB GUADALAJARA (200 M2)

Extraordinaria oportunidad de arrendamiento en una de las colonias mas arboladas y codiciadas de Guadalajara. Espacios generosos que ya no se encuentran en construcciones nuevas.

Ficha Tecnica:
- Superficie: 200 m2 habitables.
- 3 amplias recamaras, cada una con bano completo y vestidor.
- Medio bano de visitas para area social.
- 3.5 banos en total.
- Sala y comedor de gran tamano con ventilacion cruzada y vistas arboladas.
- Cocina integral cerrada con alacena y barra de trabajo.
- Cuarto de servicio con bano completo y area de lavado.
- 2 cajones de estacionamiento independientes y techados.

Renta mensual: $40,000 MXN con mantenimiento incluido.
Requisitos: Poliza juridica, comprobantes de ingresos y aval.
Contactanos para coordinar recorrido presencial."""),
            'variante_2_estilo_vida': clean_no_emojis("""VIVE CON AMPLITUD Y CONFORT EN COUNTRY CLUB (200 M2)

Disfruta del privilegio de vivir en Country Club en un departamento que te ofrece la amplitud de una casa y la seguridad de una torre privada.

Atributos de vida:
- Espacios reales de 200 metros cuadrados.
- 3 habitaciones con privacidad absoluta y 3.5 banos.
- Entorno apacible, rodeado de areas verdes y con facil acceso a Providencia y Av. Americas.
- Edificio tranquilo con excelente mantenimiento y vigilancia continua.

Canon de renta: $40,000 MXN al mes.
Contacta directamente para conocer este departamento unico en su categoria."""),
            'variante_3_inversion': clean_no_emojis("""OPORTUNIDAD DE RENTA EN LA MEJOR ZONA DE GUADALAJARA: COUNTRY CLUB

Renta mensual de $40,000 MXN por 200 metros cuadrados habitables en Country Club. Relacion precio por metro cuadrado inigualable en el mercado de arrendamiento de la zona.

- 3 recamaras completas con closets y bano propio.
- 3.5 banos.
- Sala de estar familiar y comedor espacioso.
- Estacionamiento techado y seguridad las 24 horas.

Disponibilidad inmediata. Informes y citas con atencion profesional previa confirmacion.""")
        }
    },
    {
        'folder_name': '05_torre_opera_depto_renta',
        'id': 'TORRE-OPERA-RNT',
        'nombre_oficial': 'Departamento de Lujo en Torre Opera Puerta de Hierro',
        'tipo_inmueble': 'departamento',
        'operacion': 'Renta',
        'precio_formato': '$45,000 MXN / mes',
        'ubicacion': 'Torre Opera, Puerta de Hierro / Andares, Zapopan',
        'superficie': '155 m2 habitables',
        'recamaras': 3,
        'banos': 3.5,
        'cocheras': 2,
        'descripcion_corta': 'Exclusivo departamento en Torre Opera con 3 habitaciones, 3.5 banos y amenidades de primer nivel en Puerta de Hierro.',
        'descripciones': {
            'variante_1_ejecutiva': clean_no_emojis("""DEPARTAMENTO EN RENTA EN TORRE OPERA PUERTA DE HIERRO

Residencia vertical disponible en una de las torres residenciales mas elegantes y exclusivas del distrito financiero y corporativo de Andares.

Caracteristicas:
- 3 amplias recamaras con bano privado y carpinteria fina.
- 3.5 banos completos con acabados de marmol y canceleria de cristal templado.
- Sala y comedor con ventanales de piso a techo y terraza privada con vista privilegiada.
- Cocina integral de diseno equipada con barra desayunadora de granito.
- Cuarto de lavado integrado.
- 2 cajones de estacionamiento en sotano y bodega de almacenamiento.
- Amenidades premium: Alberca templada, gimnasio de alto rendimiento, salon de eventos, spa y estricto control de seguridad 24/7.

Renta mensual: $45,000 MXN con mantenimiento incluido.
Contrato anual con poliza juridica. Atencion ejecutiva personalizada."""),
            'variante_2_estilo_vida': clean_no_emojis("""ESTILO DE VIDA Y EXCLUSIVIDAD EN TORRE OPERA ANDARES

Vive en la zona mas vibrante y sofisticada de Zapopan. A pasos del centro comercial Andares, The Landmark y las mejores opciones gastronomicas de la ciudad.

Distribucion:
- 3 recamaras disenadas con los mas altos estandares de confort.
- 3.5 banos para comodidad de toda la familia y visitas.
- Iluminacion natural, finos acabados y aislamiento acustico.
- Torre con amenidades tipo club privado.

Renta: $45,000 MXN mensuales.
Contactanos para programar tu visita y descubrir tu proximo hogar en Puerta de Hierro."""),
            'variante_3_inversion': clean_no_emojis("""OPORTUNIDAD DE ARRENDAMIENTO EN TORRE OPERA: 3 HABITACIONES

Departamento de categoria premium en Puerta de Hierro por $45,000 MXN mensuales. Ideal para ejecutivos de empresas trasnacionales o familias que buscan el maximo confort y conectividad.

- 3 recamaras con bano independiente.
- Medio bano de visitas.
- Terraza con vista panoramica.
- Maxima seguridad y doble filtro de acceso.

Solicita informacion detallada y disponibilidad para recorrido.""")
        }
    },
    {
        'folder_name': '06_hyatt_regency_andares_renta',
        'id': 'HYATT-ANDARES-RNT',
        'nombre_oficial': 'Residencias Hyatt Regency Andares Puerta de Hierro',
        'tipo_inmueble': 'departamento',
        'operacion': 'Renta',
        'precio_formato': '$57,500 MXN / mes',
        'ubicacion': 'Residencias Hyatt Regency, Andares, Zapopan',
        'superficie': '125 m2 habitables',
        'recamaras': 2,
        'banos': 2,
        'cocheras': 2,
        'descripcion_corta': 'Vivir en las exclusivas Residencias Hyatt Regency Andares con servicios de hotel 5 estrellas, 2 recamaras y 2 banos completos.',
        'descripciones': {
            'variante_1_ejecutiva': clean_no_emojis("""RESIDENCIAS HYATT REGENCY ANDARES EN RENTA: LUJO 5 ESTRELLAS

Exclusivo departamento en piso alto dentro del complejo corporativo y residencial mas importante del occidente del pais: Hyatt Regency Andares.

Ficha Tecnica:
- 2 recamaras con bano completo privado y vestidores de lujo.
- 2 banos completos de diseno contemporaneo.
- Sala y comedor de concepto abierto con ventanales panoramicos que dominan la vista de Puerta de Hierro.
- Cocina integral equipada con electrodomesticos de primera linea y barra de piedra natural.
- 2 lugares de estacionamiento techados y valet parking.
- Servicios y amenidades del desarrollo: Concierge 24/7, alberca infinita, gimnasio equipado, acceso directo al centro comercial Andares y seguridad de grado internacional.

Renta mensual: $57,500 MXN con mantenimiento incluido.
Requisitos: Contrato de arrendamiento corporativo o particular con investigacion y poliza.
Comunicate para atencion ejecutiva y recorrido privado."""),
            'variante_2_estilo_vida': clean_no_emojis("""EL MEJOR ESTILO DE VIDA EN ANDARES: RESIDENCIAS HYATT

La direccion mas prestigiosa de Guadalajara. Disfruta de la comodidad de bajar de tu elevador y tener a tu disposicion las mejores tiendas de lujo, restaurantes de alta cocina y centros corporativos.

- 2 recamaras amplias y silenciosas con acabados de hotel 5 estrellas.
- 2 banos completos con griferia y marmoles importados.
- Servicios exclusivos de concierge y vigilancia de clase mundial.
- Vistas espectaculares dia y noche.

Renta: $57,500 MXN al mes.
Citas exclusivas con previa acreditacion."""),
            'variante_3_inversion': clean_no_emojis("""OPORTUNIDAD DE RENTA EN RESIDENCIAS HYATT ANDARES

Ubicacion insuperable para directivos, empresarios y diplomáticos. Departamento de 2 recamaras en la torre mas emblematica de Andares por $57,500 MXN al mes.

- 2 habitaciones master.
- 2 banos completos.
- Acabados de lujo y equipamiento total.
- Acceso controlado y amenidades de primer orden.

Contactanos para mas detalles y opciones de contratacion.""")
        }
    },
    {
        'folder_name': '07_torre_hsbc_oficinas_renta',
        'id': 'TORRE-HSBC-OFI-RNT',
        'nombre_oficial': 'Oficinas Corporativas Piso Completo Torre HSBC (934 m2)',
        'tipo_inmueble': 'oficina',
        'operacion': 'Renta',
        'precio_formato': '$448,320 MXN / mes',
        'ubicacion': 'Torre HSBC, Corredor Financiero Americas / Providencia, Guadalajara',
        'superficie': '934 m2 corporativos',
        'recamaras': 0,
        'banos': 4,
        'cocheras': 15,
        'descripcion_corta': 'Oficina corporativa clase A de 934 m2 en Torre HSBC en el Corredor Financiero de Americas con infraestructura de punta.',
        'descripciones': {
            'variante_1_ejecutiva': clean_no_emojis("""OFICINAS CORPORATIVAS EN RENTA EN TORRE HSBC (934 M2)

Instala tu corporativo, firma legal o centro de tecnologia en el corazon financiero de Guadalajara: Av. Americas y Providencia.

Ficha Tecnica:
- Superficie: 934 m2 en piso completo con acondicionamiento corporativo.
- Distribucion: Privados directivos, salas de juntas, areas operativas abiertas y recepcion.
- Sanitarios para damas y caballeros dentro del piso y en nucleo de elevadores.
- Sistema de aire acondicionado central, cableado estructurado y site de servidores.
- Cajones de estacionamiento asignados en sotano con opcion a pensiones adicionales.
- Edificio corporativo Triple A: Elevadores de alta velocidad, planta de luz de emergencia y seguridad 24/7 con control de torniquetes.

Renta mensual: $448,320 MXN mas IVA y cuota de mantenimiento.
Trato corporativo directo. Visitas guiadas para representantes y empresas."""),
            'variante_2_estilo_vida': clean_no_emojis("""PRESTIGIO Y UBICACION CORPORATIVA EN TORRE HSBC AMERICAS

La direccion comercial que proyecta la solidez y el profesionalismo que tu empresa merece en Guadalajara. En pleno distrito financiero, cerca de bancos, hoteles ejecutivos y restaurantes de primer nivel.

- 934 metros cuadrados de espacios corporativos de alto estandar.
- Vistas panoramicas a toda la Zona Metropolitana.
- Infraestructura moderna lista para adaptarse a tu operacion.

Informes y coordinacion de visitas institucionales con previa cita."""),
            'variante_3_inversion': clean_no_emojis("""ESPACIO CORPORATIVO CLASE A EN CORREDOR FINANCIERO AMERICAS

Oficinas en piso completo de 934 m2 por $448,320 MXN mensuales. Eficiencia energetica, conectividad de fibra optica redundante y accesibilidad inmediata para tus colaboradores.

- 934 m2 adaptables a cualquier distribucion corporativa.
- Torre con certificacion y estandares internacionales de seguridad.
- Estacionamiento techado y servicio de recepcion principal.

Solicita el catalogo de especificaciones tecnicas.""")
        }
    },
    {
        'folder_name': '08_americana_estudio_amueblado_renta',
        'id': 'AMERICANA-EST-RNT',
        'nombre_oficial': 'Estudio Amueblado Todo Incluido en Colonia Americana',
        'tipo_inmueble': 'departamento',
        'operacion': 'Renta',
        'precio_formato': '$16,000 MXN / mes',
        'ubicacion': 'Colonia Americana / Chapultepec, Guadalajara',
        'superficie': '45 m2 habitables',
        'recamaras': 1,
        'banos': 1,
        'cocheras': 0,
        'descripcion_corta': 'Confortable estudio amueblado todo incluido en Colonia Americana a una cuadra de Chapultepec por $16,000 al mes.',
        'descripciones': {
            'variante_1_ejecutiva': clean_no_emojis("""ESTUDIO AMUEBLADO TODO INCLUIDO EN COLONIA AMERICANA

Ideal para profesionistas, nomadas digitales o ejecutivos que buscan vivir en la colonia mas trendy y con mejor oferta cultural y gastronomica de Guadalajara.

Servicios incluidos en la renta:
- Agua, gas, electricidad e internet de alta velocidad incluidos en los $16,000 MXN mensuales.
- Cama matrimonial, buros y amplio closet.
- Bano completo de estilo moderno.
- Cocineta equipada con parrilla, frigobar, horno y utensilios basicos.
- Area de comedor/escritorio para trabajar confortablemente.
- Edificio con acceso controlado y area de lavanderia compartida.

Renta mensual: $16,000 MXN (Todo incluido).
Requisitos sencillos: Identificacion, comprobante de ingresos y deposito.
Escribenos para conocer disponibilidad y fechas de ingreso."""),
            'variante_2_estilo_vida': clean_no_emojis("""VIVE EN LA COLONIA AMERICANA CON TODO INCLUIDO

A solo unos pasos de Av. Chapultepec, cafes de especialidad, restaurantes y galerias. Disfruta de la vida urbana de Guadalajara sin preocuparte por recibos de servicios.

- Totalmente amueblado y equipado.
- Internet de alta velocidad listo para trabajar desde casa.
- Todos los servicios incluidos en una sola cuota mensual de $16,000 MXN.

Envianos un mensaje para agendar tu cita y mudarte de inmediato."""),
            'variante_3_inversion': clean_no_emojis("""CONFORTABLE ESTUDIO EN RENTA EN COLONIA AMERICANA: $16,000 MXN

Solucion practica, centrica y segura en Guadalajara. Sin sorpresas de gastos extras de luz, gas o internet.

- 1 recamara comoda y bano privado.
- Cocineta y espacio de trabajo.
- Todo incluido por $16,000 MXN al mes.

Contactanos para informes rapidos y reserva.""")
        }
    }
]

def clean_obsolete_folders(active_folder_names):
    """
    Elimina cualquier carpeta dentro de /propiedades/ que ya no esté en la lista activa.
    Retorna la lista de carpetas eliminadas.
    """
    if not os.path.exists(PROPIEDADES_DIR):
        return []
        
    existing_folders = [f for f in os.listdir(PROPIEDADES_DIR) if os.path.isdir(os.path.join(PROPIEDADES_DIR, f))]
    deleted = []
    for folder in existing_folders:
        if folder not in active_folder_names:
            full_path = os.path.join(PROPIEDADES_DIR, folder)
            print(f"🗑 Eliminando carpeta inactiva / obsoleta: {folder}")
            shutil.rmtree(full_path, ignore_errors=True)
            deleted.append(folder)
            
    if deleted:
        print(f"\n[REPORTE DEPURACIÓN] Total carpetas eliminadas: {len(deleted)}")
        for d in deleted:
            print(f"  - {d}")
    else:
        print("\n[REPORTE DEPURACIÓN] 0 carpetas eliminadas. Todas las carpetas corresponden a propiedades activas.")
        
    return deleted

def main():
    print(f"=== ORGANIZADOR Y DEPURADOR AUTÓNOMO DE PROPIEDADES ACTIVAS ===")
    print(f"Destino: {PROPIEDADES_DIR}")
    os.makedirs(PROPIEDADES_DIR, exist_ok=True)
    
    # 1. Depurar carpetas que ya no están activas
    active_folder_names = set(p['folder_name'] for p in CATALOGO_PROPIEDADES)
    deleted_folders = clean_obsolete_folders(active_folder_names)
    
    # 2. Generar/actualizar paquetes de propiedades activas
    total_creadas = 0
    for prop in CATALOGO_PROPIEDADES:
        folder_path = os.path.join(PROPIEDADES_DIR, prop['folder_name'])
        desc_path = os.path.join(folder_path, 'descripciones')
        fotos_path = os.path.join(folder_path, 'fotografias')
        
        os.makedirs(desc_path, exist_ok=True)
        os.makedirs(fotos_path, exist_ok=True)
        
        # Guardar variantes individuales sin emojis
        for v_name, v_text in prop['descripciones'].items():
            txt_file = os.path.join(desc_path, f"{v_name}.txt")
            with open(txt_file, 'w', encoding='utf-8') as f:
                f.write(v_text)
                
        # Guardar resumen en markdown
        md_file = os.path.join(desc_path, "todas_las_variantes.md")
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(f"# Descripciones: {prop['nombre_oficial']}\n")
            f.write(f"**Precio:** {prop['precio_formato']} | **Operacion:** {prop['operacion']} | **Tipo:** {prop['tipo_inmueble']}\n\n")
            f.write(f"> [!IMPORTANT]\n> Textos 100% limpios sin emojis, listos para copiar y usar en MultiGroup Poster.\n\n")
            for i, (v_name, v_text) in enumerate(prop['descripciones'].items(), 1):
                clean_title = v_name.replace('_', ' ').title()
                f.write(f"## Variante {i}: {clean_title}\n\n")
                f.write("```text\n")
                f.write(v_text)
                f.write("\n```\n\n---\n\n")
                
        # Instrucciones de fotos
        instruc_file = os.path.join(fotos_path, "INSTRUCCIONES_FOTOS.txt")
        if not os.path.exists(instruc_file):
            with open(instruc_file, 'w', encoding='utf-8') as f:
                f.write(f"# Fotografias Exclusivas para: {prop['nombre_oficial']}\n")
                f.write("Coloca aqui las fotografias correspondientes a esta propiedad en formato HD.\n\n")
                f.write("Reglas de nomenclatura para el agente de publicacion:\n")
                f.write("  01_portada_fachada.jpg  (Foto gancho inicial)\n")
                f.write("  02_sala_comedor.jpg\n")
                f.write("  03_cocina.jpg\n")
                f.write("  04_recamara_principal.jpg\n")
                f.write("  05_bano.jpg\n")
                f.write("  06_amenidades.jpg\n\n")
                f.write("Parametros tecnicos optimos: 2048 px lado mayor, formato JPG/PNG en sRGB.\n")

        # Ficha de publicacion
        routing_lists = determine_routing_lists(prop['tipo_inmueble'], prop['operacion'], prop['ubicacion'])
        ficha = {
            'propiedad_id': prop['id'],
            'nombre_oficial': prop['nombre_oficial'],
            'operacion': prop['operacion'],
            'tipo_inmueble': prop['tipo_inmueble'],
            'precio': prop['precio_formato'],
            'ubicacion': prop['ubicacion'],
            'superficie': prop['superficie'],
            'recamaras': prop['recamaras'],
            'banos': prop['banos'],
            'cocheras': prop['cocheras'],
            'estado': 'Activa',
            'rutas_locales': {
                'carpeta_raiz': os.path.relpath(folder_path, BASE_DIR),
                'descripciones': os.path.relpath(desc_path, BASE_DIR),
                'fotografias': os.path.relpath(fotos_path, BASE_DIR)
            },
            'estrategia_multigroup_poster': {
                'listas_asignadas_obligatorias': routing_lists,
                'frecuencia_recomendada': 'Semanal recurrente (2 veces por semana por grupo)',
                'dias_rotacion_sugeridos': ['Lunes', 'Jueves'] if prop['operacion'].lower() == 'venta' else ['Martes', 'Viernes'],
                'delays_seguros_segundos': '90-180 segundos entre grupos',
                'primer_comentario_whatsapp': 'Para recibir mas fotografias o agendar recorrido presencial, contactanos via WhatsApp directo: ' + whatsapp_url()
            }
        }
        ficha_file = os.path.join(folder_path, "ficha_publicacion.json")
        with open(ficha_file, 'w', encoding='utf-8') as f:
            json.dump(ficha, f, ensure_ascii=False, indent=2)
            
        print(f"✓ Paquete activo: {prop['folder_name']} ({len(routing_lists)} listas asignadas)")
        total_creadas += 1

    print(f"\nProceso finalizado. Total de paquetes activos vigentes: {total_creadas}")

if __name__ == '__main__':
    main()
