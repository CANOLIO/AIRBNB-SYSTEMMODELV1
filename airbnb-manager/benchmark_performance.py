# benchmark_performance.py
"""
Performance benchmark script to measure optimization improvements
"""
import time
import gc
import os
import sys
from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class BenchmarkResult:
    """Container for benchmark results"""
    name: str
    execution_time: float
    memory_usage: float
    iterations: int
    success: bool
    error: str = ""


class PerformanceBenchmark:
    """Performance benchmarking utility"""
    
    def __init__(self):
        self.results: List[BenchmarkResult] = []
        
    def get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0
    
    def benchmark_function(self, func, name: str, iterations: int = 1, *args, **kwargs) -> BenchmarkResult:
        """Benchmark a function execution"""
        print(f"Benchmarking {name}...")
        
        # Prepare
        gc.collect()
        initial_memory = self.get_memory_usage()
        
        start_time = time.time()
        success = True
        error = ""
        
        try:
            for i in range(iterations):
                result = func(*args, **kwargs)
                if i == 0:  # Store first result for verification
                    first_result = result
        except Exception as e:
            success = False
            error = str(e)
            print(f"  ERROR: {error}")
        
        end_time = time.time()
        final_memory = self.get_memory_usage()
        
        execution_time = end_time - start_time
        memory_diff = final_memory - initial_memory
        
        result = BenchmarkResult(
            name=name,
            execution_time=execution_time,
            memory_usage=memory_diff,
            iterations=iterations,
            success=success,
            error=error
        )
        
        self.results.append(result)
        
        if success:
            avg_time = execution_time / iterations
            print(f"  ✓ {avg_time:.4f}s avg, {memory_diff:.1f}MB memory")
        
        return result
    
    def benchmark_import_performance(self):
        """Benchmark import performance"""
        print("\n=== IMPORT PERFORMANCE ===")
        
        # Test traditional imports
        def traditional_imports():
            import tkinter as tk
            import tkinter.ttk as ttk
            import imaplib
            import email
            import sqlite3
            import re
            return True
        
        # Test lazy imports
        def lazy_imports():
            from core.lazy_loader import LazyImporter
            tk = LazyImporter('tkinter')
            ttk = LazyImporter('tkinter.ttk')
            imaplib = LazyImporter('imaplib')
            email = LazyImporter('email')
            sqlite3 = LazyImporter('sqlite3')
            re = LazyImporter('re')
            return True
        
        self.benchmark_function(traditional_imports, "Traditional Imports", 10)
        self.benchmark_function(lazy_imports, "Lazy Imports", 10)
    
    def benchmark_database_performance(self):
        """Benchmark database performance"""
        print("\n=== DATABASE PERFORMANCE ===")
        
        # Test traditional database operations
        def traditional_db_query():
            from db.database import obtener_propiedades
            return obtener_propiedades()
        
        # Test optimized database operations
        def optimized_db_query():
            from db.optimized_database import get_propiedades_optimized
            return get_propiedades_optimized()
        
        try:
            self.benchmark_function(traditional_db_query, "Traditional DB Query", 50)
        except Exception as e:
            print(f"  Traditional DB Query failed: {e}")
        
        try:
            self.benchmark_function(optimized_db_query, "Optimized DB Query (Cached)", 50)
        except Exception as e:
            print(f"  Optimized DB Query failed: {e}")
    
    def benchmark_nlp_performance(self):
        """Benchmark NLP performance"""
        print("\n=== NLP PERFORMANCE ===")
        
        test_text = """
        Hola, soy María González y estoy interesada en reservar 
        la casa de Valdivia para el 15 de marzo al 20 de marzo.
        Somos 4 personas. Mi correo es maria@email.com y mi 
        teléfono es +56 9 1234 5678. Confirmo la reserva.
        """
        
        # Test traditional NLP
        def traditional_nlp():
            try:
                from core.nlp_engine import NLPEngine
                engine = NLPEngine()
                names = engine.extract_names(test_text)
                dates = engine.extract_dates(test_text)
                return len(names) + len(dates)
            except Exception:
                return 0
        
        # Test optimized NLP
        def optimized_nlp():
            from core.optimized_nlp import optimized_nlp
            names = optimized_nlp.extract_names_optimized(test_text)
            dates = optimized_nlp.extract_dates_optimized(test_text)
            return len(names) + len(dates)
        
        self.benchmark_function(traditional_nlp, "Traditional NLP", 100)
        self.benchmark_function(optimized_nlp, "Optimized NLP (Cached)", 100)
    
    def benchmark_memory_operations(self):
        """Benchmark memory operations"""
        print("\n=== MEMORY OPERATIONS ===")
        
        # Test object creation without pooling
        def create_objects_traditional():
            objects = []
            for i in range(1000):
                objects.append({
                    'list': [],
                    'dict': {},
                    'string': f"item_{i}"
                })
            return len(objects)
        
        # Test object creation with pooling
        def create_objects_pooled():
            from utils.memory_optimizer import get_pooled_list, get_pooled_dict, return_to_pool
            objects = []
            for i in range(1000):
                list_obj = get_pooled_list()
                dict_obj = get_pooled_dict()
                objects.append({
                    'list': list_obj,
                    'dict': dict_obj,
                    'string': f"item_{i}"
                })
                # Return objects to pool
                return_to_pool(list_obj)
                return_to_pool(dict_obj)
            return len(objects)
        
        self.benchmark_function(create_objects_traditional, "Traditional Object Creation", 10)
        self.benchmark_function(create_objects_pooled, "Pooled Object Creation", 10)
    
    def run_all_benchmarks(self):
        """Run all performance benchmarks"""
        print("AIRBNB MANAGER - PERFORMANCE BENCHMARK")
        print("=" * 50)
        
        start_time = time.time()
        
        # Individual benchmarks
        self.benchmark_import_performance()
        self.benchmark_database_performance()
        self.benchmark_nlp_performance()
        self.benchmark_memory_operations()
        
        total_time = time.time() - start_time
        
        # Summary
        print(f"\n=== BENCHMARK SUMMARY ===")
        print(f"Total benchmark time: {total_time:.2f} seconds")
        print(f"Total tests run: {len(self.results)}")
        
        successful_tests = [r for r in self.results if r.success]
        failed_tests = [r for r in self.results if not r.success]
        
        print(f"Successful: {len(successful_tests)}")
        print(f"Failed: {len(failed_tests)}")
        
        if failed_tests:
            print("\nFailed tests:")
            for test in failed_tests:
                print(f"  - {test.name}: {test.error}")
        
        # Performance comparisons
        print(f"\n=== PERFORMANCE IMPROVEMENTS ===")
        self.analyze_improvements()
    
    def analyze_improvements(self):
        """Analyze and report performance improvements"""
        comparisons = [
            ("Traditional Imports", "Lazy Imports"),
            ("Traditional DB Query", "Optimized DB Query (Cached)"),
            ("Traditional NLP", "Optimized NLP (Cached)"),
            ("Traditional Object Creation", "Pooled Object Creation")
        ]
        
        for traditional, optimized in comparisons:
            trad_result = next((r for r in self.results if r.name == traditional and r.success), None)
            opt_result = next((r for r in self.results if r.name == optimized and r.success), None)
            
            if trad_result and opt_result:
                time_improvement = ((trad_result.execution_time - opt_result.execution_time) / 
                                  trad_result.execution_time * 100)
                memory_improvement = trad_result.memory_usage - opt_result.memory_usage
                
                print(f"\n{optimized.replace(' (Cached)', '')}:")
                print(f"  Time improvement: {time_improvement:+.1f}%")
                print(f"  Memory difference: {memory_improvement:+.1f}MB")
    
    def save_results(self, filename: str = "benchmark_results.txt"):
        """Save benchmark results to file"""
        with open(filename, 'w') as f:
            f.write("AIRBNB MANAGER - PERFORMANCE BENCHMARK RESULTS\n")
            f.write("=" * 50 + "\n\n")
            
            for result in self.results:
                f.write(f"Test: {result.name}\n")
                f.write(f"Success: {result.success}\n")
                f.write(f"Execution Time: {result.execution_time:.4f}s\n")
                f.write(f"Memory Usage: {result.memory_usage:.1f}MB\n")
                f.write(f"Iterations: {result.iterations}\n")
                if result.error:
                    f.write(f"Error: {result.error}\n")
                f.write("-" * 30 + "\n")
        
        print(f"\nResults saved to {filename}")


def main():
    """Main benchmark execution"""
    # Change to airbnb-manager directory
    if os.path.basename(os.getcwd()) != 'airbnb-manager':
        if os.path.exists('airbnb-manager'):
            os.chdir('airbnb-manager')
        else:
            print("Error: airbnb-manager directory not found")
            return 1
    
    # Add current directory to path
    sys.path.insert(0, os.getcwd())
    
    try:
        benchmark = PerformanceBenchmark()
        benchmark.run_all_benchmarks()
        benchmark.save_results()
        return 0
    except Exception as e:
        print(f"Benchmark failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)