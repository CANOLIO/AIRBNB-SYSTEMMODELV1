# core/lazy_loader.py
"""
Lazy loading utility to reduce startup time by deferring heavy imports
"""
import importlib
from typing import Any, Optional


class LazyImporter:
    """Lazy import utility class that defers module loading until first access"""
    
    def __init__(self, module_name: str, attribute: Optional[str] = None):
        self.module_name = module_name
        self.attribute = attribute
        self._module = None
        self._loaded = False
    
    def __call__(self, *args, **kwargs):
        """Enable callable lazy imports"""
        obj = self._get_object()
        if callable(obj):
            return obj(*args, **kwargs)
        return obj
    
    def __getattr__(self, name):
        """Delegate attribute access to the lazily loaded module/object"""
        obj = self._get_object()
        return getattr(obj, name)
    
    def _get_object(self) -> Any:
        """Load the module/object if not already loaded"""
        if not self._loaded:
            self._module = importlib.import_module(self.module_name)
            self._loaded = True
        
        if self.attribute:
            return getattr(self._module, self.attribute)
        return self._module


# Commonly used lazy imports for the application
class LazyImports:
    """Central registry for lazy imports"""
    
    # GUI components (heavy tkinter imports)
    tkinter = LazyImporter('tkinter')
    ttk = LazyImporter('tkinter.ttk')
    messagebox = LazyImporter('tkinter.messagebox')
    
    # Email handling (heavy imaplib imports)
    imaplib = LazyImporter('imaplib')
    email = LazyImporter('email')
    smtplib = LazyImporter('smtplib')
    
    # Utility libraries
    threading = LazyImporter('threading')
    webbrowser = LazyImporter('webbrowser')
    pyperclip = LazyImporter('pyperclip')
    
    # Database
    sqlite3 = LazyImporter('sqlite3')
    
    # NLP and text processing
    re = LazyImporter('re')
    unicodedata = LazyImporter('unicodedata')
    difflib = LazyImporter('difflib')


def lazy_import(module_name: str, attribute: Optional[str] = None) -> LazyImporter:
    """Create a lazy import for a module or specific attribute"""
    return LazyImporter(module_name, attribute)


# Decorator for lazy method initialization
def lazy_property(func):
    """Decorator that makes a property lazy-loaded"""
    attr_name = f'_lazy_{func.__name__}'
    
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)
    
    return property(wrapper)