# utils/memory_optimizer.py
"""
Memory optimization utilities to reduce memory usage and improve performance
"""
import gc
import weakref
import sys
import threading
import time
from typing import Any, Dict, List, Optional, Callable, TypeVar, Generic
from functools import wraps
from collections import defaultdict, deque

T = TypeVar('T')


class ObjectPool(Generic[T]):
    """Object pool to reuse objects and reduce memory allocation overhead"""
    
    def __init__(self, factory: Callable[[], T], max_size: int = 100):
        self.factory = factory
        self.max_size = max_size
        self.pool = deque(maxlen=max_size)
        self.active_objects = weakref.WeakSet()
        self._lock = threading.Lock()
    
    def get(self) -> T:
        """Get an object from the pool or create a new one"""
        with self._lock:
            if self.pool:
                obj = self.pool.popleft()
            else:
                obj = self.factory()
            
            self.active_objects.add(obj)
            return obj
    
    def return_object(self, obj: T):
        """Return an object to the pool"""
        with self._lock:
            if len(self.pool) < self.max_size:
                # Reset object state if it has a reset method
                if hasattr(obj, 'reset'):
                    obj.reset()
                
                self.pool.append(obj)
            
            # Remove from active objects
            self.active_objects.discard(obj)
    
    def clear(self):
        """Clear the pool"""
        with self._lock:
            self.pool.clear()
    
    def stats(self) -> Dict[str, int]:
        """Get pool statistics"""
        with self._lock:
            return {
                'pool_size': len(self.pool),
                'active_objects': len(self.active_objects),
                'max_size': self.max_size
            }


class MemoryMonitor:
    """Monitor and track memory usage"""
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.memory_history = deque(maxlen=100)
        self.peak_memory = 0
        self.monitoring = False
        self.monitor_thread = None
        self._callbacks = []
    
    def start_monitoring(self):
        """Start memory monitoring"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Get current memory usage
                current_memory = self.get_memory_usage()
                
                # Update statistics
                self.memory_history.append({
                    'timestamp': time.time(),
                    'memory_mb': current_memory
                })
                
                if current_memory > self.peak_memory:
                    self.peak_memory = current_memory
                
                # Check for memory pressure
                if len(self.memory_history) >= 5:
                    recent_avg = sum(h['memory_mb'] for h in list(self.memory_history)[-5:]) / 5
                    if recent_avg > self.peak_memory * 0.8:  # 80% of peak
                        self._trigger_cleanup()
                
                # Call registered callbacks
                for callback in self._callbacks:
                    try:
                        callback(current_memory, self.peak_memory)
                    except Exception as e:
                        print(f"Memory monitor callback error: {e}")
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                print(f"Memory monitoring error: {e}")
                time.sleep(self.check_interval)
    
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        import psutil
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except ImportError:
            # Fallback if psutil is not available
            return sys.getsizeof(gc.get_objects()) / 1024 / 1024
    
    def _trigger_cleanup(self):
        """Trigger memory cleanup when memory pressure is detected"""
        print("Memory pressure detected, triggering cleanup...")
        gc.collect()
        
        # Additional cleanup can be added here
        from core.optimized_nlp import optimized_nlp
        from db.optimized_database import optimized_db
        
        # Clear NLP caches
        optimized_nlp.clear_cache()
        
        # Clear database caches
        optimized_db.cache.invalidate()
    
    def add_callback(self, callback: Callable[[float, float], None]):
        """Add a callback for memory events"""
        self._callbacks.append(callback)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory statistics"""
        if not self.memory_history:
            return {}
        
        current_memory = self.memory_history[-1]['memory_mb']
        avg_memory = sum(h['memory_mb'] for h in self.memory_history) / len(self.memory_history)
        
        return {
            'current_mb': current_memory,
            'peak_mb': self.peak_memory,
            'average_mb': avg_memory,
            'history_points': len(self.memory_history)
        }


class WeakCache:
    """Cache that uses weak references to avoid memory leaks"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache = weakref.WeakValueDictionary()
        self._access_order = deque()
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Get item from cache"""
        with self._lock:
            value = self._cache.get(key)
            if value is not None:
                # Move to end (most recently used)
                try:
                    self._access_order.remove(key)
                except ValueError:
                    pass
                self._access_order.append(key)
            return value
    
    def set(self, key: str, value: Any):
        """Set item in cache"""
        with self._lock:
            # Create a strong reference holder to keep the object alive
            class StrongRef:
                def __init__(self, obj):
                    self._obj = obj
                
                def get_object(self):
                    return self._obj
            
            strong_ref = StrongRef(value)
            self._cache[key] = strong_ref
            
            # Update access order
            try:
                self._access_order.remove(key)
            except ValueError:
                pass
            self._access_order.append(key)
            
            # Enforce size limit
            while len(self._access_order) > self.max_size:
                oldest_key = self._access_order.popleft()
                if oldest_key in self._cache:
                    del self._cache[oldest_key]
    
    def clear(self):
        """Clear the cache"""
        with self._lock:
            self._cache.clear()
            self._access_order.clear()
    
    def size(self) -> int:
        """Get cache size"""
        with self._lock:
            return len(self._cache)


class LazyContainer:
    """Container that loads objects lazily to save memory"""
    
    def __init__(self, loader_func: Callable[[], Any]):
        self.loader_func = loader_func
        self._value = None
        self._loaded = False
        self._lock = threading.Lock()
    
    def get(self) -> Any:
        """Get the value, loading it if necessary"""
        if not self._loaded:
            with self._lock:
                if not self._loaded:  # Double-check locking
                    self._value = self.loader_func()
                    self._loaded = True
        return self._value
    
    def unload(self):
        """Unload the value to free memory"""
        with self._lock:
            self._value = None
            self._loaded = False
    
    def is_loaded(self) -> bool:
        """Check if the value is loaded"""
        return self._loaded


class MemoryEfficientList:
    """Memory-efficient list that uses generators and lazy loading"""
    
    def __init__(self, data_source: Callable[[], List[Any]], chunk_size: int = 100):
        self.data_source = data_source
        self.chunk_size = chunk_size
        self._chunks = {}
        self._total_size = None
        self._lock = threading.Lock()
    
    def __len__(self) -> int:
        """Get total length"""
        if self._total_size is None:
            with self._lock:
                if self._total_size is None:
                    self._total_size = len(self.data_source())
        return self._total_size
    
    def __getitem__(self, index: int) -> Any:
        """Get item by index"""
        if isinstance(index, slice):
            return [self[i] for i in range(*index.indices(len(self)))]
        
        chunk_index = index // self.chunk_size
        item_index = index % self.chunk_size
        
        # Load chunk if not cached
        if chunk_index not in self._chunks:
            self._load_chunk(chunk_index)
        
        chunk = self._chunks[chunk_index]
        if item_index < len(chunk):
            return chunk[item_index]
        else:
            raise IndexError("Index out of range")
    
    def _load_chunk(self, chunk_index: int):
        """Load a specific chunk of data"""
        with self._lock:
            if chunk_index in self._chunks:
                return
            
            start_index = chunk_index * self.chunk_size
            end_index = start_index + self.chunk_size
            
            data = self.data_source()
            chunk = data[start_index:end_index]
            
            # Limit number of cached chunks
            if len(self._chunks) > 10:  # Keep only 10 chunks in memory
                oldest_chunk = min(self._chunks.keys())
                del self._chunks[oldest_chunk]
            
            self._chunks[chunk_index] = chunk
    
    def clear_cache(self):
        """Clear cached chunks"""
        with self._lock:
            self._chunks.clear()
            self._total_size = None


# Global memory monitor instance
memory_monitor = MemoryMonitor(check_interval=30)


def memory_efficient(func):
    """Decorator to make functions more memory efficient"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Run garbage collection before heavy operations
        gc.collect()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            # Clean up after heavy operations
            gc.collect()
    
    return wrapper


def profile_memory(func):
    """Decorator to profile memory usage of functions"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        initial_memory = memory_monitor.get_memory_usage()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            final_memory = memory_monitor.get_memory_usage()
            memory_diff = final_memory - initial_memory
            
            if memory_diff > 10:  # Log if more than 10MB difference
                print(f"Function {func.__name__} used {memory_diff:.2f}MB memory")
    
    return wrapper


# Object pools for commonly used objects
string_pool = ObjectPool(lambda: "", max_size=50)
list_pool = ObjectPool(lambda: [], max_size=20)
dict_pool = ObjectPool(lambda: {}, max_size=20)


def get_pooled_string() -> str:
    """Get a pooled string object"""
    return string_pool.get()


def get_pooled_list() -> List:
    """Get a pooled list object"""
    return list_pool.get()


def get_pooled_dict() -> Dict:
    """Get a pooled dictionary object"""
    return dict_pool.get()


def return_to_pool(obj: Any):
    """Return an object to its appropriate pool"""
    if isinstance(obj, str):
        string_pool.return_object(obj)
    elif isinstance(obj, list):
        obj.clear()  # Reset the list
        list_pool.return_object(obj)
    elif isinstance(obj, dict):
        obj.clear()  # Reset the dict
        dict_pool.return_object(obj)


def optimize_memory():
    """Run comprehensive memory optimization"""
    print("Running memory optimization...")
    
    # Force garbage collection
    collected = gc.collect()
    print(f"Garbage collector freed {collected} objects")
    
    # Clear various caches
    try:
        from core.optimized_nlp import optimized_nlp
        optimized_nlp.clear_cache()
        print("Cleared NLP caches")
    except ImportError:
        pass
    
    try:
        from db.optimized_database import optimized_db
        optimized_db.cache.invalidate()
        print("Cleared database caches")
    except ImportError:
        pass
    
    # Clear object pools
    string_pool.clear()
    list_pool.clear()
    dict_pool.clear()
    print("Cleared object pools")
    
    # Get memory stats
    final_memory = memory_monitor.get_memory_usage()
    print(f"Memory usage after optimization: {final_memory:.2f}MB")