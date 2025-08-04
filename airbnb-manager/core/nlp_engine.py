# core/nlp_engine.py
import re
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import unicodedata

class NLPEngine:
    def __init__(self):
        # Modelos lingüísticos mejorados
        self.name_patterns = self._build_name_patterns()
        self.date_patterns = self._build_date_patterns()
        self.property_patterns = self._build_property_patterns()
        self.capacity_patterns = self._build_capacity_patterns()
        self.confirmation_patterns = self._build_confirmation_patterns()

        # Diccionarios mejorados
        self.spanish_months = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }

        # Palabras comunes que NO son nombres
        self.common_non_names = {
            'propiedad', 'casa', 'depto', 'airbnb', 'reserva', 'confirmo',
            'hola', 'buenas', 'tardes', 'noches', 'gracias', 'favor',
            'necesito', 'quiero', 'deseo', 'me', 'mi', 'nos', 'nuestra',
            'mensaje', 'consulta', 'pregunta', 'duda', 'ayuda', 'información',
            'disponible', 'libre', 'ocupado', 'fechas', 'fecha', 'precio',
            'costo', 'valor', 'pagar', 'pago', 'dinero', 'efectivo',
            'tarjeta', 'transferencia', 'deposito', 'depósito', 'caución',
            'garantía', 'checkin', 'checkout', 'entrada', 'salida',
            'hospedar', 'alojar', 'quedar', 'tomar', 'reservar', 'alquilar',
            'persona', 'personas', 'huésped', 'huéspedes', 'invitado', 'invitados',
            'día', 'días', 'noche', 'noches', 'semana', 'semanas',
            'octubre', 'noviembre', 'diciembre', 'enero', 'febrero', 'marzo',
            'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre'
        }

        # Nombres comunes en español chileno
        self.common_spanish_names = {
            'juan', 'maria', 'pedro', 'ana', 'carlos', 'luisa', 'jose', 'carmen',
            'miguel', 'laura', 'francisco', 'sofia', 'antonio', 'lucia', 'manuel',
            'paula', 'fernando', 'valentina', 'ricardo', 'camila', 'diego', 'andrea',
            'roberto', 'patricia', 'felipe', 'veronica', 'sebastian', 'natalia',
            'gonzalo', 'constanza', 'matias', 'francisca', 'nicolas', 'macarena',
            'cristian', 'marcela', 'mauricio', 'claudia', 'oscar', 'monica',
            'fabian', 'rojas', 'guzman', 'fabianrojas', 'guzmann'
        }

        print("NLPEngine inicializado con modelos lingüísticos mejorados")

    def _build_name_patterns(self):
        """Construye patrones mejorados para detección de nombres"""
        return [
            # Patrones explícitos de identificación
            r'(?:me\s+llamo|mi\s+nombre\s+es|soy)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})',
            r'(?:nombre\s+completo[:\s]+)([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})',

            # Patrones de saludo formal
            r'(?:hola|buenas\s+(?:tardes|noches))[,.\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})',

            # Patrones contextuales
            r'(?:atentamente|saludos|cordialmente)[,.\s]+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})',

            # Patrones de firma (última línea)
            r'(?:^|\n)([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,2})(?:\s*$|\n)',
        ]

    def _build_date_patterns(self):
        """Construye patrones mejorados para detección de fechas"""
        return [
            # Fechas por rango con meses
            r'(?:del?\s+)?(\d{1,2})\s+(?:al?\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)',

            # Fechas desde/hasta con meses
            r'(?:desde\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+(?:hasta\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)',

            # Fechas por duración
            r'(?:desde\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+por\s+(\d+)\s+(?:d[ií]as?|noches?)',

            # Fechas entre
            r'entre\s+el\s+(\d{1,2})\s+y\s+(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)',

            # Fechas estándar
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',

            # Fechas con "de" (15 de octubre)
            r'(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)',
        ]

    def _build_property_patterns(self):
        """Construye patrones para detección de propiedades"""
        return [
            # Patrones explícitos de propiedad
            r'(?:propiedad|casa|depto|departamento|airbnb|alojamiento)\s+(?:en\s+)?([A-Za-zÁÉÍÓÚÑáéíóúñ0-9\s]+?)(?:\s+del?|\s+al?|\s+para|\s+con|\s+de|\s+y|\s*,|\s*\.)',

            # Patrones contextuales de interés
            r'(?:me\s+interesa|quiero|deseo|me\s+gustaría)\s+(?:reservar\s+)?([A-Za-zÁÉÍÓÚÑáéíóúñ0-9\s]+?)(?:\s+del?|\s+al?|\s+para|\s+con|\s+de|\s+y|\s*,|\s*\.)',

            # Patrones de ubicación
            r'(?:en|ubicado\s+en|situado\s+en)\s+([A-Za-zÁÉÍÓÚÑáéíóúñ0-9\s]+?)(?:\s+del?|\s+al?|\s+para|\s+con|\s+de|\s+y|\s*,|\s*\.)',
        ]

    def _build_capacity_patterns(self):
        """Construye patrones para detección de capacidad"""
        return [
            # Patrones explícitos de capacidad
            r'(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?|pax|invitados?)',
            r'para\s+(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?|pax)',
            r'(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?|pax)\s*(?:son|ser[íi]an|vamos|somos)',

            # Patrones contextuales
            r'(?:nos\s+hospedaremos|nos\s+alojaremos|vamos\s+a\s+ser)\s+(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?)',
            r'(?:somos|seremos)\s+(\d+)\s*(?:personas?|hu[eé]spedes?|huespedes?)',
        ]

    def _build_confirmation_patterns(self):
        """Construye patrones para detección de confirmaciones"""
        return [
            r'\b(confirmo|reservo|acepto|ok|s[ií]|perfecto|genial|bien)\b',
            r'\b(tomamos|reservamos|me\s+quedo|nos\s+quedamos)\b',
            r'\b(quiero|deseo)\s+(?:reservar|tomar|quedarme|hospedarme)\b',
        ]

    def extract_names(self, text):
        """Extrae nombres con validación semántica avanzada"""
        text_normalized = self._normalize_text(text)
        names_found = []

        for pattern in self.name_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                name = match if isinstance(match, str) else match[0] if match else ""
                if name and self._validate_name(name):
                    names_found.append(name.strip())

        # Si no hay patrones claros, buscar nombres al inicio
        if not names_found:
            names_from_context = self._extract_names_from_context(text)
            names_found.extend(names_from_context)

        # Eliminar duplicados y validar
        unique_names = list(set(names_found))
        validated_names = [name for name in unique_names if self._validate_name(name)]

        print(f"Nombres extraídos: {validated_names}")
        return validated_names

    def _extract_names_from_context(self, text):
        """Extrae nombres del contexto cuando no hay patrones claros"""
        lines = text.split('\n')
        potential_names = []

        # Buscar en las primeras líneas
        for i, line in enumerate(lines[:3]):  # Primeras 3 líneas
            line_clean = line.strip('.,!?;:').strip()
            words = line_clean.split()

            if words:
                # Caso 1: Línea corta que empieza con mayúscula
                if len(line_clean) < 30 and line_clean[0].isupper():
                    first_word = words[0].strip('.,!?;:').capitalize()
                    if self._is_potential_name(first_word):
                        # Verificar si hay apellido
                        full_name = first_word
                        if len(words) > 1:
                            second_word = words[1].strip('.,!?;:').capitalize()
                            if self._is_potential_name(second_word) and len(second_word) > 2:
                                full_name += ' ' + second_word
                        potential_names.append(full_name)
                        break

                # Caso 2: Frase de saludo
                if any(greeting in line_clean.lower() for greeting in ['hola', 'buenas', 'saludos']):
                    # Buscar palabra capitalizada después del saludo
                    for j, word in enumerate(words):
                        if word.strip('.,!?;:').isalpha() and word[0].isupper():
                            potential_name = word.strip('.,!?;:')
                            if self._is_potential_name(potential_name):
                                full_name = potential_name
                                # Buscar apellido
                                if j + 1 < len(words):
                                    next_word = words[j + 1].strip('.,!?;:').capitalize()
                                    if self._is_potential_name(next_word) and len(next_word) > 2:
                                        full_name += ' ' + next_word
                                potential_names.append(full_name)
                                break

        return potential_names

    def _validate_name(self, name):
        """Valida que sea un nombre real con múltiples criterios"""
        if not name or not isinstance(name, str):
            return False

        name_clean = name.strip('.,!?;:').strip()

        # Longitud razonable
        if len(name_clean) < 2 or len(name_clean) > 50:
            return False

        # Dividir en palabras
        words = name_clean.split()

        # Máximo 3 palabras (nombre + apellido + segundo apellido)
        if len(words) > 3:
            return False

        # Validar cada palabra
        for word in words:
            word_clean = word.strip('.,!?;:').strip()

            # Debe comenzar con mayúscula
            if not word_clean or not word_clean[0].isupper():
                return False

            # No debe contener números
            if any(char.isdigit() for char in word_clean):
                return False

            # No debe ser palabra común que no sea nombre
            word_lower = word_clean.lower()
            if word_lower in self.common_non_names and word_lower not in self.common_spanish_names:
                return False

            # Debe tener al menos 2 caracteres
            if len(word_clean) < 2:
                return False

            # Validar caracteres especiales
            if not re.match(r'^[A-ZÁÉÍÓÚÑa-záéíóúñ]+$', word_clean):
                return False

        # Si pasa todas las validaciones
        return True

    def _is_potential_name(self, word):
        """Verifica si una palabra es potencialmente un nombre"""
        if not word or len(word) < 2:
            return False

        word_clean = word.strip('.,!?;:').strip().lower()

        # No debe ser palabra común que no sea nombre
        if word_clean in self.common_non_names and word_clean not in self.common_spanish_names:
            return False

        # Debe ser palabra común que sí sea nombre o tener estructura de nombre
        if word_clean in self.common_spanish_names:
            return True

        # Debe comenzar con mayúscula si es la primera palabra
        if word[0].isupper() and len(word) >= 2:
            return True

        return False

    def extract_dates(self, text):
        """Extrae fechas con múltiples patrones y validación"""
        text_lower = text.lower()
        dates_found = []

        # Patrón 1: "del 8 al 9 de octubre"
        pattern1 = r'(?:del?\s+)?(\d{1,2})\s+(?:al?\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)'
        matches1 = re.findall(pattern1, text_lower)
        for match in matches1:
            try:
                day_start = int(match[0])
                day_end = int(match[1])
                month_name = match[2].lower()
                month_num = self.spanish_months.get(month_name)

                if month_num:
                    year = self._get_appropriate_year(month_num)
                    start_date = f"{year}-{month_num:02d}-{day_start:02d}"
                    end_date = f"{year}-{month_num:02d}-{day_end:02d}"
                    dates_found.extend([start_date, end_date])
            except:
                pass

        # Patrón 2: "desde el 8 de octubre hasta el 9 de octubre"
        pattern2 = r'(?:desde\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+(?:hasta\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)'
        matches2 = re.findall(pattern2, text_lower)
        for match in matches2:
            try:
                day_start = int(match[0])
                month_start_name = match[1].lower()
                day_end = int(match[2])
                month_end_name = match[3].lower()

                month_start_num = self.spanish_months.get(month_start_name)
                month_end_num = self.spanish_months.get(month_end_name)

                if month_start_num and month_end_num:
                    year_start = self._get_appropriate_year(month_start_num)
                    year_end = self._get_appropriate_year(month_end_num)

                    start_date = f"{year_start}-{month_start_num:02d}-{day_start:02d}"
                    end_date = f"{year_end}-{month_end_num:02d}-{day_end:02d}"
                    dates_found.extend([start_date, end_date])
            except:
                pass

        # Patrón 3: "desde el 8 de octubre por 2 días"
        pattern3 = r'(?:desde\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+por\s+(\d+)\s+(?:d[ií]as?|noches?)'
        matches3 = re.findall(pattern3, text_lower)
        for match in matches3:
            try:
                day_start = int(match[0])
                month_name = match[1].lower()
                days = int(match[2])
                month_num = self.spanish_months.get(month_name)

                if month_num:
                    year = self._get_appropriate_year(month_num)
                    start_date = f"{year}-{month_num:02d}-{day_start:02d}"
                    start_obj = datetime.strptime(start_date, '%Y-%m-%d')
                    end_obj = start_obj + timedelta(days=days - 1)
                    end_date = end_obj.strftime('%Y-%m-%d')
                    dates_found.extend([start_date, end_date])
            except:
                pass

        # Patrón 4: Fechas estándar
        standard_patterns = [r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})']
        for pattern in standard_patterns:
            matches = re.findall(pattern, text)
            dates_found.extend(matches)

        # Normalizar fechas
        normalized_dates = []
        for date_str in dates_found:
            normalized = self._normalize_date(date_str)
            if normalized:
                normalized_dates.append(normalized)

        return sorted(list(set(normalized_dates)))

    def _get_appropriate_year(self, month_num):
        """Determina año apropiado"""
        current_month = datetime.now().month
        current_year = datetime.now().year

        # Si el mes es menor que el actual y estamos cerca del final del año
        if month_num < current_month and current_month >= 10:
            return current_year + 1
        return current_year

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
                    month_num = self.spanish_months.get(month.lower())
                    if month_num:
                        year = self._get_appropriate_year(month_num)
                        return f"{year}-{month_num:02d}-{int(day):02d}"
        except:
            pass

        return None

    def extract_properties(self, text):
        """Extrae propiedades con validación contextual"""
        text_lower = text.lower()
        properties_found = []

        # Buscar patrones de propiedad
        for pattern in self.property_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                prop_text = match if isinstance(match, str) else match[0] if match else ""
                if prop_text:
                    # Limpiar y validar
                    prop_clean = prop_text.strip('.,!?;:').strip()
                    if prop_clean and len(prop_clean) > 2:
                        # Evitar palabras comunes que no son propiedades
                        if not any(word in prop_clean.lower() for word in self.common_non_names):
                            properties_found.append(prop_clean)

        return list(set(properties_found))

    def extract_capacity(self, text):
        """Extrae capacidad de personas"""
        text_lower = text.lower()

        # Buscar patrones de capacidad
        for pattern in self.capacity_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                try:
                    capacity = int(match) if isinstance(match, str) else int(match[0]) if match else 0
                    if 1 <= capacity <= 20:  # Rango razonable
                        return capacity
                except:
                    continue

        return None

    def detect_confirmation(self, text):
        """Detecta si es confirmación de reserva"""
        text_lower = text.lower()

        # Buscar patrones de confirmación
        for pattern in self.confirmation_patterns:
            if re.search(pattern, text_lower):
                # Verificar contexto de reserva
                reservation_context = ['reserva', 'propiedad', 'casa', 'alojamiento', 'airbnb']
                if any(context in text_lower for context in reservation_context):
                    return True

        return False

    def _normalize_text(self, text):
        """Normaliza texto para mejor procesamiento"""
        # Normalizar caracteres unicode
        text = unicodedata.normalize('NFKD', text)

        # Eliminar caracteres especiales problemáticos
        text = re.sub(r'[^\w\sáéíóúñÁÉÍÓÚÑ.,!?;:-]', ' ', text)

        # Normalizar espacios
        text = re.sub(r'\s+', ' ', text)

        return text.strip()

    def fuzzy_match(self, text1, text2, threshold=0.8):
        """Comparación difusa de textos"""
        similarity = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
        return similarity >= threshold


def extract_dates(self, text):
    """Extrae fechas con múltiples patrones y validación mejorada"""
    print(f"Extrayendo fechas de: '{text[:100]}'...")
    text_lower = text.lower()
    dates_found = []

    # Patrón 1: "desde el 8 hasta el 9 de octubre" (PATRÓN DEL MENSAJE REAL)
    pattern1 = r'(?:desde\s+el\s+)?(\d{1,2})\s+(?:hasta\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)'
    matches1 = re.findall(pattern1, text_lower)
    print(f"Patrón 1 matches: {matches1}")
    for match in matches1:
        try:
            day_start = int(match[0])
            day_end = int(match[1]) if match[1] else day_start + 1  # Default +1 día
            month_name = match[2].lower()
            month_num = self.spanish_months.get(month_name)

            if month_num:
                year = self._get_appropriate_year(month_num)
                start_date = f"{year}-{month_num:02d}-{day_start:02d}"
                end_date = f"{year}-{month_num:02d}-{day_end:02d}"
                dates_found.extend([start_date, end_date])
                print(f"Fechas encontradas patrón 1: {start_date}, {end_date}")
        except Exception as e:
            print(f"Error patrón 1: {e}")
            pass

    # Patrón 2: "del 8 al 9 de octubre" (PATRÓN ALTERNATIVO)
    pattern2 = r'(?:del?\s+)?(\d{1,2})\s+(?:al?\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)'
    matches2 = re.findall(pattern2, text_lower)
    print(f"Patrón 2 matches: {matches2}")
    for match in matches2:
        try:
            day_start = int(match[0])
            day_end = int(match[1])
            month_name = match[2].lower()
            month_num = self.spanish_months.get(month_name)

            if month_num:
                year = self._get_appropriate_year(month_num)
                start_date = f"{year}-{month_num:02d}-{day_start:02d}"
                end_date = f"{year}-{month_num:02d}-{day_end:02d}"
                dates_found.extend([start_date, end_date])
                print(f"Fechas encontradas patrón 2: {start_date}, {end_date}")
        except Exception as e:
            print(f"Error patrón 2: {e}")
            pass

    # Patrón 3: "desde el 8 de octubre hasta el 9 de octubre"
    pattern3 = r'(?:desde\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+(?:hasta\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)'
    matches3 = re.findall(pattern3, text_lower)
    print(f"Patrón 3 matches: {matches3}")
    for match in matches3:
        try:
            day_start = int(match[0])
            month_start_name = match[1].lower()
            day_end = int(match[2])
            month_end_name = match[3].lower()

            month_start_num = self.spanish_months.get(month_start_name)
            month_end_num = self.spanish_months.get(month_end_name)

            if month_start_num and month_end_num:
                year_start = self._get_appropriate_year(month_start_num)
                year_end = self._get_appropriate_year(month_end_num)

                start_date = f"{year_start}-{month_start_num:02d}-{day_start:02d}"
                end_date = f"{year_end}-{month_end_num:02d}-{day_end:02d}"
                dates_found.extend([start_date, end_date])
                print(f"Fechas encontradas patrón 3: {start_date}, {end_date}")
        except Exception as e:
            print(f"Error patrón 3: {e}")
            pass

    # Patrón 4: "desde el 8 de octubre por 2 días"
    pattern4 = r'(?:desde\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+por\s+(\d+)\s+(?:d[ií]as?|noches?)'
    matches4 = re.findall(pattern4, text_lower)
    print(f"Patrón 4 matches: {matches4}")
    for match in matches4:
        try:
            day_start = int(match[0])
            month_name = match[1].lower()
            days = int(match[2])
            month_num = self.spanish_months.get(month_name)

            if month_num:
                year = self._get_appropriate_year(month_num)
                start_date = f"{year}-{month_num:02d}-{day_start:02d}"
                start_obj = datetime.strptime(start_date, '%Y-%m-%d')
                end_obj = start_obj + timedelta(days=days-1)
                end_date = end_obj.strftime('%Y-%m-%d')
                dates_found.extend([start_date, end_date])
                print(f"Fechas encontradas patrón 4: {start_date}, {end_date}")
        except Exception as e:
            print(f"Error patrón 4: {e}")
            pass

    # Patrón 5: Fechas estándar
    standard_patterns = [r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})']
    for pattern in standard_patterns:
        matches = re.findall(pattern, text)
        dates_found.extend(matches)
        print(f"Fechas estándar encontradas: {matches}")

    # Normalizar fechas
    normalized_dates = []
    for date_str in dates_found:
        normalized = self._normalize_date(date_str)
        if normalized:
            normalized_dates.append(normalized)
            print(f"Fecha normalizada: {normalized}")

    unique_dates = sorted(list(set(normalized_dates)))
    print(f"Fechas únicas encontradas: {unique_dates}")
    return unique_dates


def debug_date_extraction(self, text):
    """Función de debug para ver qué está pasando con la extracción de fechas"""
    print(f"\n=== DEBUG DATE EXTRACTION ===")
    print(f"Texto: {text}")
    print(f"Texto (lower): {text.lower()}")

    # Probar cada patrón individualmente
    patterns_to_test = [
        (r'(?:desde\s+el\s+)?(\d{1,2})\s+(?:hasta\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)',
         "Patrón 1: desde X hasta Y de mes"),
        (r'(?:del?\s+)?(\d{1,2})\s+(?:al?\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)', "Patrón 2: del X al Y de mes"),
        (r'(?:desde\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+(?:hasta\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)',
         "Patrón 3: desde X de mes hasta Y de mes"),
        (r'(?:desde\s+el\s+)?(\d{1,2})\s+de\s+([a-zA-Záéíóúñ]+)\s+por\s+(\d+)\s+(?:d[ií]as?|noches?)',
         "Patrón 4: desde X de mes por N días"),
    ]

    for pattern, description in patterns_to_test:
        print(f"\n{description}")
        print(f"Patrón: {pattern}")
        matches = re.findall(pattern, text.lower())
        print(f"Matches: {matches}")

        for match in matches:
            print(f"  Match encontrado: {match}")

    print("================================\n")
# Instancia global
nlp_engine = NLPEngine()