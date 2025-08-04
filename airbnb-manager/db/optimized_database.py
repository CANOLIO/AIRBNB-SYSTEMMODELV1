# db/optimized_database.py
"""
Optimized database operations with connection pooling, caching, and batch processing
"""
import sqlite3
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
from functools import wraps
from datetime import datetime, timedelta
from contextlib import contextmanager


class ConnectionPool:
    """SQLite connection pool to reduce connection overhead"""
    
    def __init__(self, database_path: str, max_connections: int = 10):
        self.database_path = database_path
        self.max_connections = max_connections
        self._pool = []
        self._in_use = set()
        self._lock = threading.Lock()
    
    def get_connection(self) -> sqlite3.Connection:
        """Get a connection from the pool"""
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
                self._in_use.add(conn)
                return conn
            
            if len(self._in_use) < self.max_connections:
                conn = sqlite3.connect(self.database_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row  # Enable named column access
                self._in_use.add(conn)
                return conn
            
            # Wait for connection to become available
            time.sleep(0.01)
            return self.get_connection()
    
    def return_connection(self, conn: sqlite3.Connection):
        """Return a connection to the pool"""
        with self._lock:
            if conn in self._in_use:
                self._in_use.remove(conn)
                self._pool.append(conn)
    
    @contextmanager
    def get_cursor(self):
        """Context manager for database operations"""
        conn = self.get_connection()
        try:
            cursor = conn.cursor()
            yield cursor
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            self.return_connection(conn)


class QueryCache:
    """Simple query result cache with TTL"""
    
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.default_ttl = default_ttl
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result"""
        with self._lock:
            if key in self.cache:
                result, timestamp, ttl = self.cache[key]
                if time.time() - timestamp < ttl:
                    return result
                else:
                    del self.cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Cache a result"""
        with self._lock:
            ttl = ttl or self.default_ttl
            self.cache[key] = (value, time.time(), ttl)
    
    def invalidate(self, pattern: str = None):
        """Invalidate cache entries"""
        with self._lock:
            if pattern:
                keys_to_remove = [k for k in self.cache.keys() if pattern in k]
                for key in keys_to_remove:
                    del self.cache[key]
            else:
                self.cache.clear()


class OptimizedDatabase:
    """Optimized database interface with pooling and caching"""
    
    def __init__(self, database_path: str = 'data/reservas.db'):
        self.pool = ConnectionPool(database_path)
        self.cache = QueryCache()
        self._prepared_statements = {}
    
    def _cache_key(self, query: str, params: Tuple) -> str:
        """Generate cache key for query and parameters"""
        return f"{hash(query)}_{hash(params)}"
    
    def execute_cached_query(self, query: str, params: Tuple = (), ttl: int = 300) -> List[sqlite3.Row]:
        """Execute a SELECT query with caching"""
        cache_key = self._cache_key(query, params)
        
        # Try cache first
        cached_result = self.cache.get(cache_key)
        if cached_result is not None:
            return cached_result
        
        # Execute query
        with self.pool.get_cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchall()
        
        # Cache result
        self.cache.set(cache_key, result, ttl)
        return result
    
    def execute_write_query(self, query: str, params: Tuple = ()) -> int:
        """Execute INSERT, UPDATE, or DELETE query"""
        with self.pool.get_cursor() as cursor:
            cursor.execute(query, params)
            
            # Invalidate related cache entries
            table_name = self._extract_table_name(query)
            if table_name:
                self.cache.invalidate(table_name)
            
            return cursor.lastrowid or cursor.rowcount
    
    def execute_batch(self, query: str, params_list: List[Tuple]) -> List[int]:
        """Execute batch operations efficiently"""
        with self.pool.get_cursor() as cursor:
            results = []
            for params in params_list:
                cursor.execute(query, params)
                results.append(cursor.lastrowid or cursor.rowcount)
            
            # Invalidate cache
            table_name = self._extract_table_name(query)
            if table_name:
                self.cache.invalidate(table_name)
            
            return results
    
    def _extract_table_name(self, query: str) -> Optional[str]:
        """Extract table name from SQL query for cache invalidation"""
        query_lower = query.lower().strip()
        
        if query_lower.startswith('insert into'):
            return query_lower.split('insert into')[1].split()[0].strip()
        elif query_lower.startswith('update'):
            return query_lower.split('update')[1].split('set')[0].strip()
        elif query_lower.startswith('delete from'):
            return query_lower.split('delete from')[1].split()[0].strip()
        
        return None


# Global optimized database instance
optimized_db = OptimizedDatabase()


def cached_query(ttl: int = 300):
    """Decorator for caching database queries"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(sorted(kwargs.items())))}"
            
            # Try cache first
            cached_result = optimized_db.cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            optimized_db.cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator


# Optimized query functions
@cached_query(ttl=600)  # Cache for 10 minutes
def get_propiedades_optimized() -> List[sqlite3.Row]:
    """Get all properties with caching"""
    query = """
        SELECT id, nombre, direccion, capacidad, precio_noche, sector, ciudad
        FROM propiedades 
        ORDER BY nombre
    """
    return optimized_db.execute_cached_query(query)


@cached_query(ttl=300)  # Cache for 5 minutes
def get_reservas_optimized(limit: int = 100) -> List[sqlite3.Row]:
    """Get recent reservations with caching"""
    query = """
        SELECT r.*, p.nombre as propiedad_nombre
        FROM reservas r
        LEFT JOIN propiedades p ON r.propiedad_id = p.id
        ORDER BY r.fecha_inicio DESC
        LIMIT ?
    """
    return optimized_db.execute_cached_query(query, (limit,))


@cached_query(ttl=120)  # Cache for 2 minutes
def get_mensajes_no_respondidos_optimized() -> List[sqlite3.Row]:
    """Get unresponded messages with caching"""
    query = """
        SELECT * FROM mensajes 
        WHERE respondido = 0 
        ORDER BY fecha_recibido DESC
    """
    return optimized_db.execute_cached_query(query)


def bulk_insert_messages(messages: List[Dict]) -> List[int]:
    """Efficiently insert multiple messages"""
    query = """
        INSERT INTO mensajes (asunto, remitente, contenido, fecha_recibido, respondido)
        VALUES (?, ?, ?, ?, ?)
    """
    params_list = [
        (msg['asunto'], msg['remitente'], msg['contenido'], 
         msg['fecha_recibido'], msg.get('respondido', 0))
        for msg in messages
    ]
    return optimized_db.execute_batch(query, params_list)


def verificar_disponibilidad_optimized(propiedad_id: int, fecha_inicio: str, fecha_fin: str) -> bool:
    """Check availability with caching"""
    cache_key = f"disponibilidad_{propiedad_id}_{fecha_inicio}_{fecha_fin}"
    cached_result = optimized_db.cache.get(cache_key)
    
    if cached_result is not None:
        return cached_result
    
    query = """
        SELECT COUNT(*) as conflictos
        FROM reservas 
        WHERE propiedad_id = ? 
        AND estado != 'cancelada'
        AND (
            (fecha_inicio <= ? AND fecha_fin > ?) OR
            (fecha_inicio < ? AND fecha_fin >= ?) OR
            (fecha_inicio >= ? AND fecha_fin <= ?)
        )
    """
    
    with optimized_db.pool.get_cursor() as cursor:
        cursor.execute(query, (propiedad_id, fecha_inicio, fecha_inicio, 
                              fecha_fin, fecha_fin, fecha_inicio, fecha_fin))
        result = cursor.fetchone()
        disponible = result['conflictos'] == 0
    
    # Cache for 5 minutes
    optimized_db.cache.set(cache_key, disponible, 300)
    return disponible