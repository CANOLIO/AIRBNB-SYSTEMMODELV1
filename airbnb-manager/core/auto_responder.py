# core/auto_responder.py
import re
from datetime import datetime, timedelta
from db.database import verificar_disponibilidad, obtener_propiedad_por_id, buscar_propiedades_por_criterios, \
    obtener_propiedades


class AutoResponder:
    def __init__(self):
        self.faq_responses = {
            'fumar': "No se permite fumar dentro de las propiedades. Existen áreas designadas para fumadores en el exterior.",
            'mascotas': "No se permiten mascotas en nuestras propiedades, salvo que se indique lo contrario en la descripción.",
            'cancelacion': "Nuestra política de cancelación es de 48 horas antes del check-in para obtener reembolso completo.",
            'checkin': "El check-in es a partir de las 15:00 horas. Si necesitas un horario especial, por favor avísanos con anticipación.",
            'checkout': "El check-out es antes de las 11:00 horas.",
            'limpieza': "La propiedad se entrega completamente limpia y se cobra una tarifa de limpieza que está incluida en el precio.",
            'deposito': "Se requiere un depósito de garantía de $50.000 CLP que se devuelve al check-out si no hay daños.",
            'wifi': "Todas nuestras propiedades incluyen WiFi de alta velocidad gratuito.",
            'estacionamiento': "El estacionamiento es gratuito y está disponible para nuestros huéspedes.",
            'ubicacion': "Nuestras propiedades están ubicadas en zonas céntricas de Valdivia, cerca de atracciones principales."
        }

        self.faq_keywords = {
            'fumar': ['fumar', 'fumo', 'cigarro', 'tabaco'],
            'mascotas': ['mascota', 'perro', 'gato', 'animal'],
            'cancelacion': ['cancelar', 'cancelación', 'reembolso', 'devolución'],
            'checkin': ['check in', 'llegada', 'entrada', 'hora entrada'],
            'checkout': ['check out', 'salida', 'hora salida'],
            'limpieza': ['limpiar', 'limpieza', 'aseo'],
            'deposito': ['depósito', 'garantía', 'caución'],
            'wifi': ['wifi', 'internet', 'red', 'conexión'],
            'estacionamiento': ['estacionar', 'parking', 'auto', 'vehículo'],
            'ubicacion': ['ubicación', 'dirección', 'dónde', 'donde', 'cerca']
        }

        self.months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

        self.cities = ['valdivia', 'corral', 'lanco', 'los lagos', 'máfil', 'mariquina', 'paillaco', 'antofagasta']

    def analizar_mensaje(self, mensaje):
        """Analiza mensaje y extrae información relevante"""
        cuerpo = mensaje.get('cuerpo', '').lower()
        asunto = mensaje.get('asunto', '').lower()
        texto_completo = cuerpo + ' ' + asunto

        # Buscar fechas en el mensaje
        fechas_info = self.extraer_fechas_inteligentes(texto_completo)

        # Buscar preguntas frecuentes
        faq_tipo = self.detectar_faq(texto_completo)

        # Buscar información de búsqueda de propiedades
        criterios_busqueda = self.extraer_criterios_busqueda_inteligente(texto_completo)

        # Determinar tipo de mensaje
        if fechas_info and len(fechas_info) >= 2:
            return {
                'tipo': 'consulta_disponibilidad',
                'fechas': fechas_info,
                'propiedad_id': 1,  # Valor por defecto, se puede mejorar
                'criterios_busqueda': criterios_busqueda
            }
        elif faq_tipo:
            return {
                'tipo': 'pregunta_frecuente',
                'faq_tipo': faq_tipo
            }
        elif criterios_busqueda:
            return {
                'tipo': 'busqueda_propiedades',
                'criterios_busqueda': criterios_busqueda
            }
        else:
            return {
                'tipo': 'requiere_revision_manual',
                'motivo': 'mensaje_no_clasificado'
            }

    def extraer_fechas_inteligentes(self, texto):
        """Extrae fechas de manera más inteligente y flexible"""
        fechas_encontradas = []
        texto_lower = texto.lower()

        # Patrón 1: "del 12 al 15 de agosto"
        patron1 = r'del?\s+(\d{1,2})\s+al?\s+(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)'
        matches1 = re.findall(patron1, texto_lower, re.IGNORECASE)
        for match in matches1:
            try:
                dia_inicio = int(match[0])
                dia_fin = int(match[1])
                mes = match[2].lower()
                mes_num = self.meses_a_numero(mes)
                if mes_num:
                    año = datetime.now().year
                    fecha_inicio = f"{año}-{mes_num:02d}-{dia_inicio:02d}"
                    fecha_fin = f"{año}-{mes_num:02d}-{dia_fin:02d}"
                    fechas_encontradas.extend([fecha_inicio, fecha_fin])
            except:
                pass

        # Patrón 2: "desde el 10 de septiembre por 5 días"
        patron2 = r'desde\s+el\s+(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+por\s+(\d+)\s+d[ií]as?'
        matches2 = re.findall(patron2, texto_lower, re.IGNORECASE)
        for match in matches2:
            try:
                dia_inicio = int(match[0])
                mes = match[1].lower()
                dias = int(match[2])
                mes_num = self.meses_a_numero(mes)
                if mes_num:
                    año = datetime.now().year
                    fecha_inicio = f"{año}-{mes_num:02d}-{dia_inicio:02d}"
                    fecha_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                    fecha_fin_obj = fecha_obj + timedelta(days=dias - 1)
                    fecha_fin = fecha_fin_obj.strftime('%Y-%m-%d')
                    fechas_encontradas.extend([fecha_inicio, fecha_fin])
            except:
                pass

        # Patrón 3: "entre el 5 y 8 de julio"
        patron3 = r'entre\s+el\s+(\d{1,2})\s+y\s+(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)'
        matches3 = re.findall(patron3, texto_lower, re.IGNORECASE)
        for match in matches3:
            try:
                dia_inicio = int(match[0])
                dia_fin = int(match[1])
                mes = match[2].lower()
                mes_num = self.meses_a_numero(mes)
                if mes_num:
                    año = datetime.now().year
                    fecha_inicio = f"{año}-{mes_num:02d}-{dia_inicio:02d}"
                    fecha_fin = f"{año}-{mes_num:02d}-{dia_fin:02d}"
                    fechas_encontradas.extend([fecha_inicio, fecha_fin])
            except:
                pass

        # Patrón 4: "3 noches desde el 1 de septiembre"
        patron4 = r'(\d+)\s+noches?\s+desde\s+el\s+(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)'
        matches4 = re.findall(patron4, texto_lower, re.IGNORECASE)
        for match in matches4:
            try:
                noches = int(match[0])
                dia_inicio = int(match[1])
                mes = match[2].lower()
                mes_num = self.meses_a_numero(mes)
                if mes_num:
                    año = datetime.now().year
                    fecha_inicio = f"{año}-{mes_num:02d}-{dia_inicio:02d}"
                    fecha_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                    fecha_fin_obj = fecha_obj + timedelta(days=noches)
                    fecha_fin = fecha_fin_obj.strftime('%Y-%m-%d')
                    fechas_encontradas.extend([fecha_inicio, fecha_fin])
            except:
                pass

        # Patrón 5: Fechas estándar (DD/MM/YYYY, DD-MM-YYYY, etc.)
        patrones_estandar = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})'
        ]

        for patron in patrones_estandar:
            matches = re.findall(patron, texto)
            fechas_encontradas.extend(matches)

        # Convertir a formato estándar
        fechas_formateadas = []
        for fecha in fechas_encontradas:
            fecha_formateada = self.normalizar_fecha(fecha)
            if fecha_formateada:
                fechas_formateadas.append(fecha_formateada)

        # Eliminar duplicados y ordenar
        return sorted(list(set(fechas_formateadas)))

    def meses_a_numero(self, mes):
        """Convierte nombre de mes a número"""
        return self.months.get(mes, None)

    def normalizar_fecha(self, fecha_str):
        """Normaliza diferentes formatos de fecha a YYYY-MM-DD"""
        try:
            # Intentar varios formatos
            formatos = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y']

            for formato in formatos:
                try:
                    fecha_obj = datetime.strptime(fecha_str, formato)
                    return fecha_obj.strftime('%Y-%m-%d')
                except:
                    continue

            # Para fechas como "15 de marzo"
            if 'de' in fecha_str:
                partes = fecha_str.split(' de ')
                if len(partes) == 2:
                    dia = partes[0]
                    mes = partes[1]
                    mes_num = self.meses_a_numero(mes.lower())
                    if mes_num:
                        año = datetime.now().year
                        return f"{año}-{mes_num:02d}-{int(dia):02d}"

        except Exception as e:
            print(f"Error normalizando fecha {fecha_str}: {e}")
            return None

        return None

    def detectar_faq(self, texto):
        """Detecta si el mensaje contiene una pregunta frecuente"""
        texto = texto.lower()

        for faq_tipo, keywords in self.faq_keywords.items():
            for keyword in keywords:
                if keyword in texto:
                    return faq_tipo
        return None

    def extraer_criterios_busqueda_inteligente(self, texto):
        """Extrae criterios de búsqueda de propiedades de manera más inteligente"""
        criterios = {}

        # Buscar cantidad de personas (más flexible)
        personas_patterns = [
            r'(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?|pax|invitados?)',
            r'para\s+(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?|pax)',
            r'(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?|pax)\s*(?:son|ser[íi]an|vamos)'
        ]

        for pattern in personas_patterns:
            personas_match = re.search(pattern, texto)
            if personas_match:
                try:
                    criterios['capacidad_min'] = int(personas_match.group(1))
                    break
                except:
                    continue

        # Buscar sectores de Valdivia
        sectores_valdivia = [
            'isla teja', 'teja', 'las ánimas', 'animas', 'el bosque', 'bosque',
            'valdivia centro', 'centro', 'paseo ahumada', 'ahumada',
            'universidad austral', 'austral', 'hospital base', 'base',
            'costanera', 'puerto', 'barrio ingles', 'ingles'
        ]

        for sector in sectores_valdivia:
            if sector in texto:
                criterios['sector'] = sector
                break

        # Buscar ciudades
        for ciudad in self.cities:
            if ciudad in texto:
                criterios['ciudad'] = ciudad.capitalize()
                break

        # Si no se encuentra ciudad específica pero mencionan "Valdivia", usar por defecto
        if 'valdivia' in texto and 'ciudad' not in criterios:
            criterios['ciudad'] = 'Valdivia'

        return criterios

    def generar_respuesta_consulta_disponibilidad(self, consulta):
        """Genera respuesta automática para consulta de disponibilidad"""
        if len(consulta['fechas']) < 2:
            return "Por favor indique las fechas de inicio y fin de su estadía para verificar disponibilidad."

        fecha_inicio = min(consulta['fechas'][:2])  # Tomar las primeras 2 fechas
        fecha_fin = max(consulta['fechas'][:2])

        disponible = verificar_disponibilidad(
            consulta['propiedad_id'],
            fecha_inicio,
            fecha_fin
        )

        propiedad = obtener_propiedad_por_id(consulta['propiedad_id'])
        nombre_propiedad = propiedad[1] if propiedad else "la propiedad"

        if disponible:
            return f"""¡Buenas noticias!

{nombre_propiedad} está disponible del {fecha_inicio} al {fecha_fin}.

¿Desea confirmar la reserva? Para proceder con la reserva, necesitaré la siguiente información:
- Número de huéspedes
- Datos de contacto (nombre completo, teléfono, email)
- Método de pago preferido

Quedo atento(a) a su confirmación.

¡Gracias por su interés!"""
        else:
            return f"""Lamentablemente, {nombre_propiedad} no está disponible para las fechas del {fecha_inicio} al {fecha_fin}.

¿Le interesa consultar disponibilidad para otras fechas? Estaré encantado de ayudarle a encontrar las mejores opciones.

Quedo atento(a) a su respuesta."""

    def generar_respuesta_faq(self, faq_tipo):
        """Genera respuesta para pregunta frecuente"""
        return self.faq_responses.get(faq_tipo,
                                      "Gracias por su consulta. Estaré encantado de responderle lo antes posible.")

    def generar_respuesta_busqueda_propiedades(self, consulta):
        """Genera respuesta para búsqueda de propiedades"""
        criterios = consulta['criterios_busqueda']

        if criterios:
            propiedades = buscar_propiedades_por_criterios(**criterios)
        else:
            propiedades = obtener_propiedades()

        if not propiedades:
            respuesta = "Lamentablemente, no encontramos propiedades que coincidan con sus criterios"
            if 'capacidad_min' in criterios:
                respuesta += f" (mínimo {criterios['capacidad_min']} personas)"
            if 'ciudad' in criterios:
                respuesta += f" en {criterios['ciudad']}"
            elif 'sector' in criterios:
                respuesta += f" en {criterios['sector']}"
            respuesta += ".\n\n¿Desea modificar sus criterios de búsqueda?"
            return respuesta
        elif len(propiedades) == 1:
            prop = propiedades[0]
            respuesta = f"Le comparto información sobre nuestra propiedad disponible:\n\n"
            respuesta += f"🏠 {prop[1]}\n"
            respuesta += f"   Dirección: {prop[2]}\n"
            if prop[5]:  # Sector
                respuesta += f"   Sector: {prop[5]}\n"
            if prop[6]:  # Ciudad
                respuesta += f"   Ciudad: {prop[6]}\n"
            respuesta += f"   Capacidad: {prop[3]} personas\n"
            if prop[4]:
                respuesta += f"   Precio por noche: ${prop[4]:,.0f} CLP\n"
            respuesta += "\n¿Desea verificar disponibilidad para fechas específicas?\n\nQuedo atento a su respuesta."
            return respuesta
        else:
            respuesta = f"Le comparto nuestras {len(propiedades)} propiedades disponibles:\n\n"
            for i, prop in enumerate(propiedades[:5], 1):  # Limitar a 5 propiedades
                respuesta += f"{i}. {prop[1]}\n"
                respuesta += f"   Ubicación: {prop[2]}\n"
                if prop[5]:  # Sector
                    respuesta += f"   Sector: {prop[5]}\n"
                if prop[6]:  # Ciudad
                    respuesta += f"   Ciudad: {prop[6]}\n"
                respuesta += f"   Capacidad: {prop[3]} personas"
                if prop[4]:
                    respuesta += f" - ${prop[4]:,.0f}/noche"
                respuesta += "\n\n"

            if len(propiedades) > 5:
                respuesta += f"... y {len(propiedades) - 5} propiedades más.\n\n"

            respuesta += "¿Está interesado en alguna de estas propiedades? ¿Desea verificar disponibilidad para fechas específicas?\n\nQuedo atento a su respuesta."
            return respuesta


# Instancia global
auto_responder = AutoResponder()