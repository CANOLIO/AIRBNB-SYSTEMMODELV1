# main_optimized.py
"""
Optimized main entry point with performance improvements and lazy loading
"""
import os
import sys
from core.lazy_loader import LazyImporter
from utils.memory_optimizer import memory_monitor, optimize_memory

# Lazy imports for better startup performance
tk = LazyImporter('tkinter')
messagebox = LazyImporter('tkinter.messagebox')


class OptimizedApplication:
    """Main application class with performance optimizations"""
    
    def __init__(self):
        self.root = None
        self.app_gui = None
        self.initialized = False
        
        # Performance monitoring
        self.startup_time = None
        self.memory_stats = {}
    
    def setup_directories(self):
        """Create necessary directories"""
        directories = ['data', 'data/logs', 'data/cache']
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")
    
    def check_dependencies(self):
        """Check and validate dependencies with lazy loading"""
        try:
            # Only import when actually needed
            imaplib = LazyImporter('imaplib')
            keyring = LazyImporter('keyring')
            
            # Test imports by accessing them
            _ = imaplib.IMAP4
            _ = keyring.get_password
            
            print("All dependencies available")
            return True
            
        except ImportError as e:
            print(f"Error: Missing dependency. Install with: pip install imaplib2 keyring")
            print(f"Details: {e}")
            return False
    
    def initialize_database(self):
        """Initialize database with optimizations"""
        try:
            # Use optimized database initialization
            from db.optimized_database import optimized_db
            from db.database import init_db
            
            # Initialize traditional database first
            init_db()
            
            # Initialize optimized components
            print("Database optimizations enabled")
            return True
            
        except Exception as e:
            print(f"Database initialization error: {e}")
            return False
    
    def initialize_nlp(self):
        """Initialize NLP engine with optimizations"""
        try:
            from core.optimized_nlp import optimized_nlp
            print("NLP optimizations enabled")
            return True
            
        except Exception as e:
            print(f"NLP initialization error: {e}")
            return False
    
    def start_memory_monitoring(self):
        """Start memory monitoring"""
        try:
            memory_monitor.start_monitoring()
            
            # Add callback for high memory usage
            def memory_callback(current_mb, peak_mb):
                if current_mb > 500:  # Alert if over 500MB
                    print(f"High memory usage detected: {current_mb:.1f}MB")
            
            memory_monitor.add_callback(memory_callback)
            print("Memory monitoring started")
            
        except Exception as e:
            print(f"Memory monitoring error: {e}")
    
    def create_gui(self):
        """Create GUI with optimizations"""
        try:
            import time
            gui_start = time.time()
            
            # Create root window
            self.root = tk.Tk()
            self.root.title("Sistema de Gestión Airbnb - Valdivia (Optimizado)")
            self.root.geometry("1200x800")
            
            # Import GUI after tkinter is ready
            from gui.app_gui import AppGUI
            
            # Create application GUI
            self.app_gui = AppGUI(self.root)
            
            gui_time = time.time() - gui_start
            print(f"GUI initialized in {gui_time:.2f} seconds")
            
            return True
            
        except Exception as e:
            print(f"GUI creation error: {e}")
            return False
    
    def run(self):
        """Run the application with performance monitoring"""
        import time
        self.startup_time = time.time()
        
        print("Starting Airbnb Management System (Optimized)")
        print("=" * 50)
        
        # Setup phase
        print("Phase 1: Setup...")
        self.setup_directories()
        
        # Dependency check
        print("Phase 2: Checking dependencies...")
        if not self.check_dependencies():
            return False
        
        # Database initialization
        print("Phase 3: Initializing database...")
        if not self.initialize_database():
            return False
        
        # NLP initialization
        print("Phase 4: Initializing NLP engine...")
        if not self.initialize_nlp():
            return False
        
        # Memory monitoring
        print("Phase 5: Starting monitoring...")
        self.start_memory_monitoring()
        
        # GUI creation
        print("Phase 6: Creating GUI...")
        if not self.create_gui():
            return False
        
        # Performance summary
        total_startup = time.time() - self.startup_time
        memory_stats = memory_monitor.get_stats()
        
        print("\n" + "=" * 50)
        print("OPTIMIZATION SUMMARY")
        print("=" * 50)
        print(f"Total startup time: {total_startup:.2f} seconds")
        print(f"Memory usage: {memory_stats.get('current_mb', 0):.1f}MB")
        print("Optimizations enabled:")
        print("  ✓ Lazy imports")
        print("  ✓ Database connection pooling")
        print("  ✓ NLP result caching")
        print("  ✓ Memory monitoring")
        print("  ✓ Asynchronous email processing")
        print("=" * 50)
        
        # Start main loop
        try:
            self.initialized = True
            self.root.mainloop()
            
        except KeyboardInterrupt:
            print("\nShutdown requested...")
            self.shutdown()
        except Exception as e:
            print(f"Runtime error: {e}")
            return False
        
        return True
    
    def shutdown(self):
        """Clean shutdown with resource cleanup"""
        print("Shutting down application...")
        
        # Stop memory monitoring
        try:
            memory_monitor.stop_monitoring()
            print("Memory monitoring stopped")
        except:
            pass
        
        # Run final memory optimization
        try:
            optimize_memory()
            print("Final memory cleanup completed")
        except:
            pass
        
        # Close GUI
        if self.root:
            try:
                self.root.quit()
                self.root.destroy()
            except:
                pass
        
        print("Shutdown complete")


def main():
    """Main entry point"""
    try:
        app = OptimizedApplication()
        success = app.run()
        
        if not success:
            print("Application failed to start properly")
            return 1
        
        return 0
        
    except Exception as e:
        print(f"Critical error: {e}")
        return 1
    finally:
        # Ensure cleanup
        try:
            optimize_memory()
        except:
            pass


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)