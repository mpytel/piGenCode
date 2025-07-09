# Performance optimizations for syncCode

import hashlib
import pickle
import concurrent.futures
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta

class SyncCache:
    """Cache system for syncCode to avoid redundant processing"""
    
    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path.cwd() / ".pigencode_cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.cache_file = self.cache_dir / "sync_cache.pkl"
        self.cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load cache from disk"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
        except Exception as e:
            printIt(f"Warning: Could not load sync cache: {e}", lable.WARN)
        return {}
    
    def _save_cache(self):
        """Save cache to disk"""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache_data, f)
        except Exception as e:
            printIt(f"Warning: Could not save sync cache: {e}", lable.WARN)
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file content for change detection"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""
    
    def should_sync_file(self, python_file: Path, piseed_file: Path) -> bool:
        """Check if file needs syncing based on modification times and content hashes"""
        cache_key = str(python_file)
        
        # Get current file info
        try:
            py_stat = python_file.stat()
            py_mtime = py_stat.st_mtime
            py_hash = self._get_file_hash(python_file)
            
            seed_stat = piseed_file.stat()
            seed_mtime = seed_stat.st_mtime
        except Exception:
            # If we can't get file stats, assume sync is needed
            return True
        
        # Check cache
        if cache_key in self.cache_data:
            cached_info = self.cache_data[cache_key]
            
            # If Python file hasn't changed since last sync, skip
            if (cached_info.get('py_mtime') == py_mtime and 
                cached_info.get('py_hash') == py_hash and
                cached_info.get('seed_mtime') == seed_mtime):
                return False
        
        return True
    
    def record_sync(self, python_file: Path, piseed_file: Path, changes: List[str]):
        """Record successful sync in cache"""
        cache_key = str(python_file)
        
        try:
            py_stat = python_file.stat()
            seed_stat = piseed_file.stat()
            
            self.cache_data[cache_key] = {
                'py_mtime': py_stat.st_mtime,
                'py_hash': self._get_file_hash(python_file),
                'seed_mtime': seed_stat.st_mtime,
                'last_sync': datetime.now().isoformat(),
                'changes_count': len(changes)
            }
            
            self._save_cache()
        except Exception as e:
            printIt(f"Warning: Could not record sync in cache: {e}", lable.WARN)
    
    def clear_cache(self):
        """Clear the sync cache"""
        self.cache_data = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
        printIt("Sync cache cleared", lable.INFO)
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        return {
            'total_entries': len(self.cache_data),
            'cache_file_size': self.cache_file.stat().st_size if self.cache_file.exists() else 0,
            'oldest_entry': min((entry['last_sync'] for entry in self.cache_data.values()), default=None),
            'newest_entry': max((entry['last_sync'] for entry in self.cache_data.values()), default=None)
        }

def parallel_sync_files(files_and_seeds: List[Tuple[Path, Path, str]], max_workers: int = 4) -> Dict:
    """
    Sync multiple files in parallel for better performance.
    files_and_seeds: List of (python_file, piseed_file, file_type) tuples
    """
    results = {
        'processed': 0,
        'changes': 0,
        'errors': 0,
        'skipped': 0
    }
    
    def sync_single_file(file_info):
        """Sync a single file - wrapper for parallel execution"""
        python_file, piseed_file, file_type = file_info
        
        try:
            if file_type == 'def':
                changes = syncPythonDefToSeed(python_file, piseed_file)
            else:
                changes = syncPythonClassToSeed(python_file, piseed_file)
            
            return {
                'file': str(python_file),
                'changes': changes or [],
                'success': True,
                'error': None
            }
        except Exception as e:
            return {
                'file': str(python_file),
                'changes': [],
                'success': False,
                'error': str(e)
            }
    
    # Process files in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {
            executor.submit(sync_single_file, file_info): file_info[0] 
            for file_info in files_and_seeds
        }
        
        # Collect results
        for future in concurrent.futures.as_completed(future_to_file):
            file_path = future_to_file[future]
            
            try:
                result = future.result()
                
                if result['success']:
                    results['processed'] += 1
                    results['changes'] += len(result['changes'])
                    
                    if result['changes']:
                        printIt(f"Synced {len(result['changes'])} changes from {Path(result['file']).name}", lable.INFO)
                else:
                    results['errors'] += 1
                    printIt(f"Error syncing {Path(result['file']).name}: {result['error']}", lable.ERROR)
                    
            except Exception as e:
                results['errors'] += 1
                printIt(f"Unexpected error with {file_path.name}: {e}", lable.ERROR)
    
    return results

def incremental_sync_with_cache(cache: SyncCache, options: dict = None) -> Dict:
    """
    Perform incremental sync using cache to skip unchanged files.
    """
    options = options or {}
    results = {
        'processed': 0,
        'skipped_cache': 0,
        'changes': 0,
        'errors': 0
    }
    
    # Collect all files to potentially sync
    files_to_check = []
    
    # Get files from configured directories
    piClassesDir = Path(getKeyItem("piClassGCDir", "piClasses"))
    piDefsDir = Path(getKeyItem("piDefGCDir", "piDefs"))
    
    if piClassesDir.exists():
        for py_file in piClassesDir.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                className = py_file.stem
                piseed_file = findPiClassGCSeedFile(className)
                if piseed_file:
                    files_to_check.append((py_file, piseed_file, 'class'))
    
    if piDefsDir.exists():
        for py_file in piDefsDir.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                defName = py_file.stem
                piseed_file = findPiDefGCSeedFile(defName)
                if piseed_file:
                    files_to_check.append((py_file, piseed_file, 'def'))
    
    printIt(f"Checking {len(files_to_check)} files for changes...", lable.INFO)
    
    # Filter files that need syncing
    files_to_sync = []
    for py_file, piseed_file, file_type in files_to_check:
        if options.get('force', False) or cache.should_sync_file(py_file, piseed_file):
            files_to_sync.append((py_file, piseed_file, file_type))
        else:
            results['skipped_cache'] += 1
    
    printIt(f"Found {len(files_to_sync)} files that need syncing", lable.INFO)
    printIt(f"Skipped {results['skipped_cache']} files (no changes detected)", lable.DEBUG)
    
    if not files_to_sync:
        printIt("No files need syncing", lable.INFO)
        return results
    
    # Sync files (in parallel if many files)
    if len(files_to_sync) > 5 and not options.get('no_parallel', False):
        printIt("Using parallel processing for better performance...", lable.INFO)
        sync_results = parallel_sync_files(files_to_sync, max_workers=min(4, len(files_to_sync)))
        results.update(sync_results)
    else:
        # Sequential processing
        for py_file, piseed_file, file_type in files_to_sync:
            try:
                if file_type == 'def':
                    changes = syncPythonDefToSeed(py_file, piseed_file)
                else:
                    changes = syncPythonClassToSeed(py_file, piseed_file)
                
                if changes:
                    results['changes'] += len(changes)
                    printIt(f"Synced {len(changes)} changes from {py_file.name}", lable.INFO)
                    
                    # Record in cache
                    cache.record_sync(py_file, piseed_file, changes)
                
                results['processed'] += 1
                
            except Exception as e:
                results['errors'] += 1
                printIt(f"Error syncing {py_file.name}: {e}", lable.ERROR)
    
    return results

def optimize_ast_parsing():
    """Optimize AST parsing for better performance"""
    
    # Cache compiled AST trees to avoid re-parsing
    _ast_cache = {}
    
    def cached_ast_parse(content: str, file_path: str = None) -> ast.AST:
        """Parse Python content with caching"""
        # Create cache key from content hash
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        if content_hash in _ast_cache:
            return _ast_cache[content_hash]
        
        try:
            tree = ast.parse(content)
            _ast_cache[content_hash] = tree
            
            # Limit cache size to prevent memory issues
            if len(_ast_cache) > 100:
                # Remove oldest entries
                oldest_key = next(iter(_ast_cache))
                del _ast_cache[oldest_key]
            
            return tree
        except SyntaxError as e:
            # Don't cache syntax errors
            raise e
    
    return cached_ast_parse

def batch_file_operations(operations: List[Tuple[str, Path, str]], batch_size: int = 20):
    """
    Batch file read/write operations for better I/O performance.
    operations: List of (operation_type, file_path, content) tuples
    """
    results = []
    
    for i in range(0, len(operations), batch_size):
        batch = operations[i:i + batch_size]
        batch_results = []
        
        # Process batch
        for op_type, file_path, content in batch:
            try:
                if op_type == 'read':
                    with open(file_path, 'r', encoding='utf-8') as f:
                        result = f.read()
                    batch_results.append((True, result))
                elif op_type == 'write':
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    batch_results.append((True, None))
                else:
                    batch_results.append((False, f"Unknown operation: {op_type}"))
            except Exception as e:
                batch_results.append((False, str(e)))
        
        results.extend(batch_results)
        
        # Small delay between batches to prevent I/O overload
        if i + batch_size < len(operations):
            import time
            time.sleep(0.01)
    
    return results

# Performance monitoring
class PerformanceMonitor:
    """Monitor performance of sync operations"""
    
    def __init__(self):
        self.start_time = None
        self.operation_times = {}
        self.file_sizes = {}
    
    def start_operation(self, operation_name: str):
        """Start timing an operation"""
        self.operation_times[operation_name] = {
            'start': datetime.now(),
            'end': None,
            'duration': None
        }
    
    def end_operation(self, operation_name: str):
        """End timing an operation"""
        if operation_name in self.operation_times:
            self.operation_times[operation_name]['end'] = datetime.now()
            start = self.operation_times[operation_name]['start']
            end = self.operation_times[operation_name]['end']
            self.operation_times[operation_name]['duration'] = (end - start).total_seconds()
    
    def record_file_size(self, file_path: Path):
        """Record file size for analysis"""
        try:
            size = file_path.stat().st_size
            self.file_sizes[str(file_path)] = size
        except Exception:
            pass
    
    def get_performance_report(self) -> Dict:
        """Get performance analysis report"""
        total_duration = sum(
            op['duration'] for op in self.operation_times.values() 
            if op['duration'] is not None
        )
        
        avg_file_size = sum(self.file_sizes.values()) / len(self.file_sizes) if self.file_sizes else 0
        
        return {
            'total_duration': total_duration,
            'operations': len(self.operation_times),
            'avg_operation_time': total_duration / len(self.operation_times) if self.operation_times else 0,
            'files_processed': len(self.file_sizes),
            'avg_file_size': avg_file_size,
            'largest_file': max(self.file_sizes.values()) if self.file_sizes else 0,
            'operation_breakdown': {
                name: op['duration'] for name, op in self.operation_times.items() 
                if op['duration'] is not None
            }
        }

# Usage example
def syncCodeWithPerformanceOptimizations(argParse: ArgParse):
    """syncCode with performance optimizations enabled"""
    
    # Initialize performance monitoring
    monitor = PerformanceMonitor()
    monitor.start_operation('total_sync')
    
    # Initialize cache
    cache = SyncCache()
    
    try:
        # Parse arguments
        args = argParse.parser.parse_args()
        theArgs = args.arguments
        
        options = {
            'force': '--force' in theArgs,
            'no_parallel': '--no-parallel' in theArgs,
            'clear_cache': '--clear-cache' in theArgs
        }
        
        # Clear cache if requested
        if options['clear_cache']:
            cache.clear_cache()
            return
        
        # Show cache stats
        cache_stats = cache.get_cache_stats()
        printIt(f"Cache: {cache_stats['total_entries']} entries, {cache_stats['cache_file_size']} bytes", lable.DEBUG)
        
        # Perform incremental sync
        monitor.start_operation('incremental_sync')
        results = incremental_sync_with_cache(cache, options)
        monitor.end_operation('incremental_sync')
        
        # Show results
        printIt(f"Performance Summary:", lable.INFO)
        printIt(f"  Processed: {results['processed']} files", lable.INFO)
        printIt(f"  Skipped (cached): {results['skipped_cache']} files", lable.INFO)
        printIt(f"  Changes: {results['changes']}", lable.INFO)
        printIt(f"  Errors: {results['errors']}", lable.INFO)
        
    finally:
        monitor.end_operation('total_sync')
        
        # Show performance report
        perf_report = monitor.get_performance_report()
        printIt(f"Total time: {perf_report['total_duration']:.2f}s", lable.DEBUG)
        if perf_report['files_processed'] > 0:
            printIt(f"Avg time per file: {perf_report['total_duration'] / perf_report['files_processed']:.3f}s", lable.DEBUG)
