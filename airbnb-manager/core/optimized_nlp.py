# core/optimized_nlp.py
"""
Optimized NLP Engine with caching and improved performance for natural language processing
"""
import re
import hashlib
import pickle
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from functools import lru_cache
from core.lazy_loader import lazy_property, LazyImporter

# Lazy imports for better startup performance
difflib = LazyImporter('difflib')
unicodedata = LazyImporter('unicodedata')


class OptimizedNLPEngine:
    """Enhanced NLP engine with caching and performance optimizations"""
    
    def __init__(self):
        self._pattern_cache = {}
        self._result_cache = {}
        self._max_cache_size = 1000
        
        # Pre-compile commonly used patterns for better performance
        self._compiled_patterns = self._compile_patterns()
        
        # Load dictionaries lazily
        self._spanish_months = None
        self._common_non_names = None
        self._common_spanish_names = None
    
    @lazy_property
    def spanish_months(self) -> Dict[str, int]:
        """Lazy load Spanish months dictionary"""
        return {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
        }
    
    @lazy_property
    def common_non_names(self) -> set:
        """Lazy load common non-name words"""
        return {
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
            'día', 'días', 'noche', 'noches', 'semana', 'semanas'
        }
    
    @lazy_property
    def common_spanish_names(self) -> set:
        """Lazy load common Spanish names"""
        return {
            'juan', 'maria', 'pedro', 'ana', 'carlos', 'luisa', 'jose', 'carmen',
            'miguel', 'laura', 'francisco', 'sofia', 'antonio', 'lucia', 'manuel',
            'paula', 'fernando', 'valentina', 'ricardo', 'camila', 'diego', 'andrea',
            'roberto', 'patricia', 'felipe', 'veronica', 'sebastian', 'natalia',
            'gonzalo', 'constanza', 'matias', 'francisca', 'nicolas', 'macarena',
            'cristian', 'marcela', 'mauricio', 'claudia', 'oscar', 'monica',
            'fabian', 'rojas', 'guzman', 'fabianrojas', 'guzmann'
        }
    
    def _compile_patterns(self) -> Dict[str, re.Pattern]:
        """Pre-compile regex patterns for better performance"""
        patterns = {
            'name': re.compile(r'\b[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+\b'),
            'date_dmy': re.compile(r'\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b'),
            'date_text': re.compile(r'\b(\d{1,2})\s+de\s+(\w+)(?:\s+de\s+(\d{2,4}))?\b', re.IGNORECASE),
            'capacity': re.compile(r'\b(\d+)\s*(?:persona|huésped|gente|pax)\b', re.IGNORECASE),
            'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            'phone': re.compile(r'\b(?:\+56\s*)?(?:9\s*)?(\d{4}\s*\d{4}|\d{8})\b'),
            'confirmation': re.compile(r'\b(?:confirmo|confirmado|ok|sí|si|vale|perfecto|de acuerdo)\b', re.IGNORECASE)
        }
        return patterns
    
    def _get_cache_key(self, text: str, operation: str) -> str:
        """Generate cache key for text and operation"""
        return f"{operation}_{hashlib.md5(text.encode()).hexdigest()}"
    
    def _get_cached_result(self, text: str, operation: str) -> Optional[Any]:
        """Get cached result if available"""
        cache_key = self._get_cache_key(text, operation)
        return self._result_cache.get(cache_key)
    
    def _cache_result(self, text: str, operation: str, result: Any):
        """Cache operation result"""
        if len(self._result_cache) >= self._max_cache_size:
            # Remove oldest entries (simple FIFO)
            oldest_keys = list(self._result_cache.keys())[:100]
            for key in oldest_keys:
                del self._result_cache[key]
        
        cache_key = self._get_cache_key(text, operation)
        self._result_cache[cache_key] = result
    
    @lru_cache(maxsize=500)
    def normalize_text(self, text: str) -> str:
        """Normalize text with LRU caching"""
        if not text:
            return ""
        
        # Remove accents and normalize unicode
        normalized = unicodedata.normalize('NFD', text)
        ascii_text = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
        
        # Convert to lowercase and clean
        cleaned = re.sub(r'[^\w\s]', ' ', ascii_text.lower())
        return re.sub(r'\s+', ' ', cleaned).strip()
    
    def extract_names_optimized(self, text: str) -> List[str]:
        """Extract names with caching and optimization"""
        cached_result = self._get_cached_result(text, 'names')
        if cached_result is not None:
            return cached_result
        
        names = []
        
        # Use pre-compiled pattern
        potential_names = self._compiled_patterns['name'].findall(text)
        
        for name in potential_names:
            name_lower = name.lower()
            
            # Skip if it's a common non-name word
            if name_lower in self.common_non_names:
                continue
            
            # Include if it's a known Spanish name or follows name patterns
            if (name_lower in self.common_spanish_names or 
                len(name) >= 3 and name[0].isupper()):
                names.append(name)
        
        # Remove duplicates while preserving order
        unique_names = []
        seen = set()
        for name in names:
            if name.lower() not in seen:
                unique_names.append(name)
                seen.add(name.lower())
        
        self._cache_result(text, 'names', unique_names)
        return unique_names
    
    def extract_dates_optimized(self, text: str) -> List[Tuple[str, str]]:
        """Extract dates with caching and optimization"""
        cached_result = self._get_cached_result(text, 'dates')
        if cached_result is not None:
            return cached_result
        
        dates = []
        
        # Extract numeric dates (DD/MM/YYYY or DD-MM-YYYY)
        for match in self._compiled_patterns['date_dmy'].finditer(text):
            day, month, year = match.groups()
            try:
                # Convert to standard format
                if len(year) == 2:
                    year = f"20{year}"
                date_str = f"{int(day):02d}/{int(month):02d}/{year}"
                dates.append((date_str, match.group()))
            except ValueError:
                continue
        
        # Extract text dates (1 de enero, 15 de marzo de 2024)
        for match in self._compiled_patterns['date_text'].finditer(text):
            day, month_name, year = match.groups()
            try:
                month_num = self.spanish_months.get(month_name.lower())
                if month_num:
                    current_year = datetime.now().year
                    year = int(year) if year else current_year
                    date_str = f"{int(day):02d}/{month_num:02d}/{year}"
                    dates.append((date_str, match.group()))
            except (ValueError, AttributeError):
                continue
        
        self._cache_result(text, 'dates', dates)
        return dates
    
    def extract_capacity_optimized(self, text: str) -> Optional[int]:
        """Extract capacity with caching"""
        cached_result = self._get_cached_result(text, 'capacity')
        if cached_result is not None:
            return cached_result
        
        match = self._compiled_patterns['capacity'].search(text)
        capacity = int(match.group(1)) if match else None
        
        self._cache_result(text, 'capacity', capacity)
        return capacity
    
    def extract_contact_info_optimized(self, text: str) -> Dict[str, str]:
        """Extract contact information with caching"""
        cached_result = self._get_cached_result(text, 'contact')
        if cached_result is not None:
            return cached_result
        
        contact_info = {}
        
        # Extract email
        email_match = self._compiled_patterns['email'].search(text)
        if email_match:
            contact_info['email'] = email_match.group()
        
        # Extract phone
        phone_match = self._compiled_patterns['phone'].search(text)
        if phone_match:
            contact_info['phone'] = phone_match.group()
        
        self._cache_result(text, 'contact', contact_info)
        return contact_info
    
    def detect_confirmation_optimized(self, text: str) -> bool:
        """Detect confirmation with caching"""
        cached_result = self._get_cached_result(text, 'confirmation')
        if cached_result is not None:
            return cached_result
        
        confirmation = bool(self._compiled_patterns['confirmation'].search(text))
        
        self._cache_result(text, 'confirmation', confirmation)
        return confirmation
    
    def batch_process_messages(self, messages: List[str]) -> List[Dict[str, Any]]:
        """Process multiple messages efficiently in batch"""
        results = []
        
        for message in messages:
            result = {
                'names': self.extract_names_optimized(message),
                'dates': self.extract_dates_optimized(message),
                'capacity': self.extract_capacity_optimized(message),
                'contact': self.extract_contact_info_optimized(message),
                'confirmation': self.detect_confirmation_optimized(message)
            }
            results.append(result)
        
        return results
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Get cache statistics for monitoring"""
        return {
            'cache_size': len(self._result_cache),
            'max_cache_size': self._max_cache_size,
            'normalize_cache_info': self.normalize_text.cache_info()._asdict()
        }
    
    def clear_cache(self):
        """Clear all caches"""
        self._result_cache.clear()
        self.normalize_text.cache_clear()


# Global optimized NLP engine instance
optimized_nlp = OptimizedNLPEngine()


def similarity_score_cached(text1: str, text2: str) -> float:
    """Calculate similarity score with caching"""
    cache_key = f"similarity_{hash(text1)}_{hash(text2)}"
    
    # Check if result is cached (simple dict cache for this function)
    if not hasattr(similarity_score_cached, '_cache'):
        similarity_score_cached._cache = {}
    
    if cache_key in similarity_score_cached._cache:
        return similarity_score_cached._cache[cache_key]
    
    # Calculate similarity
    normalized1 = optimized_nlp.normalize_text(text1)
    normalized2 = optimized_nlp.normalize_text(text2)
    
    similarity = difflib.SequenceMatcher(None, normalized1, normalized2).ratio()
    
    # Cache result (limit cache size)
    if len(similarity_score_cached._cache) > 500:
        similarity_score_cached._cache.clear()
    
    similarity_score_cached._cache[cache_key] = similarity
    return similarity