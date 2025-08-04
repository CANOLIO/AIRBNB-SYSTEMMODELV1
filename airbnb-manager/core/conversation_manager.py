# core/conversation_manager.py
from db.conversation_db import (
    create_or_update_conversation, get_conversation,
    update_conversation_field, get_missing_fields,
    is_confirmed, add_message_to_conversation,
    get_conversation_messages, get_conversation_id,
)
from db.database import obtener_propiedades, verificar_disponibilidad
import re
from datetime import datetime, timedelta
from core.nlp_engine import nlp_engine


class ConversationManager:
    def __init__(self):
        self.known_properties = self._load_known_properties()
        print("ConversationManager inicializado")

    def _load_known_properties(self):
        """Carga propiedades conocidas de la base de datos"""
        try:
            propiedades = obtener_propiedades()
            properties_dict = {}
            for prop in propiedades:
                # Nombre completo de la propiedad
                nombre = prop[1].lower()
                properties_dict[nombre] = {
                    'id': prop[0],
                    'nombre': prop[1],
                    'direccion': prop[2],
                    'capacidad': prop[3],
                    'precio': prop[4]
                }

                # Palabras clave del nombre
                palabras = nombre.split()
                for palabra in palabras:
                    if len(palabra) > 3:  # Solo palabras significativas
                        if palabra not in properties_dict:
                            properties_dict[palabra] = {
                                'id': prop[0],
                                'nombre': prop[1],
                                'direccion': prop[2],
                                'capacidad': prop[3],
                                'precio': prop[4]
                            }
            return properties_dict
        except Exception as e:
            print(f"Error cargando propiedades: {e}")
            return {}

    def process_message(self, message):
        """Procesa un mensaje y actualiza la conversación"""
        remitente = message.get('remitente', '')
        asunto = message.get('asunto', '')
        cuerpo = message.get('cuerpo', '')

        print(f"Procesando mensaje de {remitente} - {asunto}")
        print(f"Contenido: {cuerpo[:100]}...")

        # Crear o actualizar conversación
        conversation_id = create_or_update_conversation(remitente, asunto)

        # Guardar mensaje en la conversación
        message_data = {
            'message_id': message.get('id'),
            'sender': remitente,
            'subject': asunto,
            'body': cuerpo,
            'message_type': self._classify_message(cuerpo)
        }
        add_message_to_conversation(conversation_id, message_data)

        # Extraer y actualizar datos
        extracted_data = self._extract_message_data(cuerpo, remitente)
        print(f"Datos extraídos: {extracted_data}")

        self._update_conversation_data(conversation_id, extracted_data)

        return conversation_id

    def get_conversation_context(self, conversation_id):
        """Obtiene contexto completo de la conversación"""
        conversation = get_conversation(conversation_id)
        if conversation:
            return {
                'data': conversation,
                'faltantes': get_missing_fields(conversation_id),
                'confirmada': is_confirmed(conversation_id),
                'mensajes': get_conversation_messages(conversation_id)
            }
        return None

    def _classify_message(self, cuerpo):
        """Clasifica tipo de mensaje"""
        texto = cuerpo.lower()

        # Confirmación de reserva
        confirmation_keywords = ['confirmo', 'reservo', 'acepto', 'ok', 'sí', 'si', 'perfecto', 'quiero', 'deseo',
                                 'tomamos', 'reservamos']
        reservation_context = ['reserva', 'propiedad', 'casa', 'alojamiento', 'airbnb', 'quedarnos', 'alojarnos']

        if any(keyword in texto for keyword in confirmation_keywords):
            if any(context in texto for context in reservation_context):
                return 'confirmacion_reserva'

        # Consulta de propiedades
        property_keywords = ['propiedad', 'casa', 'depto', 'airbnb', 'alojamiento', 'quedarme', 'arrendar',
                             'interesado', 'me gustaría', 'interesa']
        if any(keyword in texto for keyword in property_keywords):
            return 'consulta_propiedades'

        # Preguntas frecuentes
        faq_keywords = ['pregunta', 'duda', 'consulta', 'fumar', 'mascota', 'cancelar', 'checkin', 'checkout']
        if any(keyword in texto for keyword in faq_keywords):
            return 'pregunta_frecuente'

        return 'consulta_general'

    def _extract_message_data(self, cuerpo, remitente):
        """Extrae datos del mensaje usando el motor NLP avanzado"""
        print(f"Extrayendo datos de: {cuerpo[:100]}...")
        data = {}

        # Usar el motor NLP para extraer datos
        from core.nlp_engine import nlp_engine

        # Extraer fechas usando NLP Engine (CORREGIDO)
        fechas = nlp_engine.extract_dates(cuerpo)  # Usar cuerpo completo, no cuerpo.lower()
        if len(fechas) >= 2:
            data['check_in'] = min(fechas[:2])
            data['check_out'] = max(fechas[:2])
            print(f"Fechas extraídas: {data['check_in']} a {data['check_out']}")
        elif len(fechas) == 1:
            data['check_in'] = fechas[0]
            print(f"Fecha de inicio extraída: {data['check_in']}")

        # Extraer capacidad usando NLP Engine
        capacidad = nlp_engine.extract_capacity(cuerpo)
        if capacidad:
            data['numero_huespedes'] = capacidad
            print(f"Capacidad extraída: {capacidad}")

        # Extraer propiedad usando NLP Engine
        propiedades = nlp_engine.extract_properties(cuerpo)
        if propiedades:
            mejor_propiedad = self._find_best_property_match(propiedades)
            if mejor_propiedad:
                data['propiedad'] = mejor_propiedad['nombre']
                data['propiedad_id'] = mejor_propiedad['id']
                print(f"Propiedad extraída: {mejor_propiedad['nombre']}")
            else:
                # Usar la primera propiedad encontrada
                data['propiedad'] = propiedades[0]
                # Buscar ID correspondiente
                for prop_name, prop_info in self.known_properties.items():
                    if propiedades[0].lower() in prop_name.lower():
                        data['propiedad_id'] = prop_info['id']
                        break
                print(f"Propiedad extraída (búsqueda directa): {propiedades[0]}")

        # Extraer nombre usando NLP Engine
        nombres = nlp_engine.extract_names(cuerpo)  # Usar cuerpo completo
        if nombres:
            data['nombre_cliente'] = nombres[0]  # Usar el primer nombre válido
            print(f"Nombre extraído: {nombres[0]}")

        # Extraer correo (del remitente)
        if remitente:
            email = self._extract_email_from_sender(remitente)
            if email:
                data['correo_cliente'] = email
                print(f"Email extraído: {email}")

        # Extraer teléfono
        telefono = self._extract_phone(cuerpo.lower())
        if telefono:
            data['telefono_cliente'] = telefono
            print(f"Teléfono extraído: {telefono}")

        print(f"DEBUG FINAL - Fechas encontradas: {fechas}")
        print(f"DEBUG FINAL - Capacidad: {capacidad}")
        print(f"DEBUG FINAL - Propiedades: {propiedades}")
        print(f"DEBUG FINAL - Nombres: {nombres}")
        print("================================")

        return data

    def _find_best_property_match(self, extracted_properties):
        """Encuentra la mejor coincidencia de propiedad"""
        if not extracted_properties:
            return None

        # Buscar coincidencias exactas o cercanas
        for extracted_prop in extracted_properties:
            extracted_prop_lower = extracted_prop.lower()

            # Buscar coincidencia exacta
            for prop_name, prop_info in self.known_properties.items():
                if nlp_engine.fuzzy_match(extracted_prop_lower, prop_name, 0.9):
                    return prop_info

            # Buscar coincidencia aproximada
            for prop_name, prop_info in self.known_properties.items():
                if nlp_engine.fuzzy_match(extracted_prop_lower, prop_name, 0.7):
                    return prop_info

        # Si no hay coincidencia, devolver la primera propiedad extraída
        if extracted_properties:
            first_prop = extracted_properties[0]
            # Buscar en propiedades conocidas
            for prop_name, prop_info in self.known_properties.items():
                if first_prop.lower() in prop_name.lower():
                    return prop_info

        return None

    def _update_conversation_data(self, conversation_id, extracted_data):
        """Actualiza datos de la conversación"""
        for key, value in extracted_data.items():
            if value:  # Solo actualizar si hay valor
                try:
                    update_conversation_field(conversation_id, key, value)
                    print(f"Campo {key} actualizado a: {value}")
                except Exception as e:
                    print(f"Error actualizando {key}: {e}")

    def _extract_dates(self, texto):
        """Extrae fechas del texto"""
        fechas_encontradas = []

        # Meses en español
        months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

        # Patrón: "del 15 al 20 de octubre"
        pattern1 = r'del?\s+(\d{1,2})\s+al?\s+(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)'
        matches1 = re.findall(pattern1, texto, re.IGNORECASE)
        print(f"Patrón 1 matches: {matches1}")
        for match in matches1:
            try:
                day_start = int(match[0])
                day_end = int(match[1])
                month_name = match[2].lower()
                month_num = months.get(month_name)

                if month_num:
                    year = datetime.now().year
                    # Ajustar año si es necesario
                    if month_num < datetime.now().month and datetime.now().month >= 10:
                        year += 1

                    fecha_inicio = f"{year}-{month_num:02d}-{day_start:02d}"
                    fecha_fin = f"{year}-{month_num:02d}-{day_end:02d}"
                    fechas_encontradas.extend([fecha_inicio, fecha_fin])
                    print(f"Fechas encontradas patrón 1: {fecha_inicio}, {fecha_fin}")
            except Exception as e:
                print(f"Error patrón 1: {e}")
                pass

        # Patrón: "desde el 10 de septiembre por 5 días"
        pattern2 = r'desde\s+el\s+(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+por\s+(\d+)\s+d[ií]as?'
        matches2 = re.findall(pattern2, texto, re.IGNORECASE)
        print(f"Patrón 2 matches: {matches2}")
        for match in matches2:
            try:
                day_start = int(match[0])
                month_name = match[1].lower()
                days = int(match[2])
                month_num = months.get(month_name)

                if month_num:
                    year = datetime.now().year
                    if month_num < datetime.now().month and datetime.now().month >= 10:
                        year += 1

                    fecha_inicio = f"{year}-{month_num:02d}-{day_start:02d}"
                    fecha_obj = datetime.strptime(fecha_inicio, '%Y-%m-%d')
                    fecha_fin_obj = fecha_obj + timedelta(days=days - 1)
                    fecha_fin = fecha_fin_obj.strftime('%Y-%m-%d')
                    fechas_encontradas.extend([fecha_inicio, fecha_fin])
                    print(f"Fechas encontradas patrón 2: {fecha_inicio}, {fecha_fin}")
            except Exception as e:
                print(f"Error patrón 2: {e}")
                pass

        # Patrón estándar
        standard_patterns = [r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})']
        for pattern in standard_patterns:
            matches = re.findall(pattern, texto)
            fechas_encontradas.extend(matches)
            print(f"Fechas estándar encontradas: {matches}")

        # Normalizar fechas
        normalized_dates = []
        for date_str in fechas_encontradas:
            normalized = self._normalize_date(date_str)
            if normalized:
                normalized_dates.append(normalized)
                print(f"Fecha normalizada: {normalized}")

        return sorted(list(set(normalized_dates)))

    def _normalize_date(self, date_str):
        """Normaliza fecha a formato YYYY-MM-DD"""
        try:
            formats = ['%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%d/%m/%y', '%d-%m-%y']

            for fmt in formats:
                try:
                    date_obj = datetime.strptime(date_str, fmt)
                    return date_obj.strftime('%Y-%m-%d')
                except:
                    continue

            # Para fechas como "15 de marzo"
            if 'de' in date_str:
                parts = date_str.split(' de ')
                if len(parts) == 2:
                    day = parts[0]
                    month = parts[1]
                    months = {
                        'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
                        'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
                        'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
                    }
                    month_num = months.get(month.lower())
                    if month_num:
                        year = datetime.now().year
                        if month_num < datetime.now().month and datetime.now().month >= 10:
                            year += 1
                        return f"{year}-{month_num:02d}-{int(day):02d}"
        except Exception as e:
            print(f"Error normalizando fecha {date_str}: {e}")
            pass

        return None

    def _extract_capacity(self, texto):
        """Extrae número de personas"""
        patterns = [
            r'(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?|pax|invitados?)',
            r'para\s+(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?|pax)'
        ]

        for pattern in patterns:
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                try:
                    capacidad = int(match.group(1))
                    print(f"Capacidad encontrada: {capacidad}")
                    return capacidad
                except:
                    continue
        return None

    def _extract_property(self, texto):
        """Extrae información de propiedad"""
        data = {}
        texto_lower = texto.lower()

        print(f"Buscando propiedad en: {texto_lower[:100]}...")

        # Buscar propiedades por nombre
        for property_name, property_info in self.known_properties.items():
            if property_name in texto_lower:
                data['propiedad'] = property_info['nombre']
                data['propiedad_id'] = property_info['id']
                print(f"Propiedad encontrada por nombre: {property_info['nombre']}")
                return data

        # Buscar por palabras clave específicas
        property_keywords = {
            'depa isla teja': 'isla teja',
            'casa regional': 'regional'
        }

        for keyword, search_term in property_keywords.items():
            if keyword in texto_lower:
                for prop_name, prop_info in self.known_properties.items():
                    if search_term in prop_name.lower():
                        data['propiedad'] = prop_info['nombre']
                        data['propiedad_id'] = prop_info['id']
                        print(f"Propiedad encontrada por keyword: {keyword} -> {prop_info['nombre']}")
                        return data
                break

        return data

    def _extract_name(self, texto):
        """Extrae nombre del cliente con mejor detección"""
        print(f"Buscando nombre en: '{texto[:100]}'...")

        # Patrones más flexibles y específicos
        patterns = [
            # Patrón 1: "Me llamo Juan Pérez"
            r'(?:me\s+llamo|mi\s+nombre\s+es|soy)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',

            # Patrón 2: "Nombre completo: Juan Pérez"
            r'(?:nombre\s+completo[:\s]+)([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)',

            # Patrón 3: "Hola, Juan Pérez"
            r'(?:hola\s*[,.\s]*)?([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*)(?:\s*[,.\n]|$)',

            # Patrón 4: "Juan Pérez," (nombre al inicio)
            r'^([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)*),?',
        ]

        for i, pattern in enumerate(patterns):
            print(f"Probando patrón {i + 1}: {pattern}")
            match = re.search(pattern, texto, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                print(f"Nombre encontrado con patrón {i + 1}: '{name}'")

                # Validar que sea un nombre real
                if len(name.split()) <= 3 and len(name) > 2:
                    # Evitar palabras clave del sistema
                    invalid_words = [
                        'propiedad', 'interesa', 'confirmo', 'reserva', 'hola', 'buenas',
                        'tardes', 'noches', 'mensaje', 'consulta', 'pregunta', 'duda'
                    ]
                    if not any(word in name.lower() for word in invalid_words):
                        clean_name = name.strip('.,!?;:')
                        print(f"Nombre válido extraído: '{clean_name}'")
                        return clean_name

        # Método alternativo: buscar nombres al inicio si no hay patrones claros
        lines = texto.split('\n')
        if lines:
            first_line = lines[0].strip()
            # Si la línea empieza con una palabra capitalizada
            words = first_line.split()
            if words:
                first_word = words[0].strip('.,!?;:').capitalize()
                # Verificar contra lista de nombres comunes
                nombres_comunes = [
                    'juan', 'maria', 'pedro', 'ana', 'carlos', 'luisa', 'fabian',
                    'roberto', 'carmen', 'jose', 'rojas', 'perez', 'gonzalez'
                ]
                if first_word.lower() in nombres_comunes:
                    full_name = first_word
                    if len(words) > 1 and words[1].strip('.,!?;:').isalpha():
                        second_word = words[1].strip('.,!?;:').capitalize()
                        if len(second_word) > 1:
                            full_name += ' ' + second_word
                    print(f"Nombre encontrado al inicio: '{full_name}'")
                    return full_name

        print("No se encontró nombre válido")
        return None

    def _extract_email_from_sender(self, remitente_str):
        """Extrae email del string del remitente"""
        import re
        email_pattern = r'<([^>]+)>|([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
        matches = re.findall(email_pattern, remitente_str)

        for match in matches:
            email = match[0] if match[0] else match[1]
            if email:
                print(f"Email extraído del remitente: {email}")
                return email

        return None

    def _extract_phone(self, texto):
        """Extrae teléfono"""
        patterns = [
            r'(?:tel[eé]fono|fono|contacto)[:\s]*([9\d\s\-\.]{8,12})',
            r'(9\s*\d{4}\s*\d{4})'
        ]

        for pattern in patterns:
            match = re.search(pattern, texto)
            if match:
                return match.group(1).strip()
        return None

    def debug_message_processing(self, cuerpo, remitente):
        """Función de debug para ver qué se está procesando"""
        print(f"\n=== DEBUG MESSAGE PROCESSING ===")
        print(f"Remitente: {remitente}")
        print(f"Cuerpo: {cuerpo}")
        print(f"Cuerpo (lower): {cuerpo.lower()}")

        # Probar extracción de nombre
        nombre = self._extract_name(cuerpo)
        print(f"Nombre extraído: {nombre}")

        # Probar otros datos
        fechas = self._extract_dates(cuerpo.lower())
        print(f"Fechas extraídas: {fechas}")

        capacidad = self._extract_capacity(cuerpo.lower())
        print(f"Capacidad extraída: {capacidad}")

        propiedad = self._extract_property(cuerpo.lower())
        print(f"Propiedad extraída: {propiedad}")
        print("================================\n")

# Instancia global
conversation_manager = ConversationManager()