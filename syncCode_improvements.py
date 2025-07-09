# Suggested improvements for syncCode functionality

def find_python_files_recursively(base_dir: Path, file_type: str = "class") -> List[Tuple[Path, str]]:
    """
    Recursively find Python files in directory tree and determine their type.
    Returns list of (file_path, detected_type) tuples.
    """
    python_files = []
    
    if not base_dir.exists():
        return python_files
    
    # Recursively find all .py files
    for py_file in base_dir.rglob("*.py"):
        # Skip __pycache__ and other system directories
        if "__pycache__" in str(py_file) or ".git" in str(py_file):
            continue
            
        # Determine file type based on content analysis
        detected_type = "class"  # default
        if file_type == "auto":
            detected_type = "def" if isPythonFileDefType(py_file) else "class"
        else:
            detected_type = file_type
            
        python_files.append((py_file, detected_type))
    
    return python_files

def syncAllChangedFilesEnhanced():
    """Enhanced version of syncAllChangedFiles with recursive directory support"""
    try:
        totalChanges = 0
        processedFiles = 0
        skippedFiles = 0
        
        # Process piClassGCDir recursively
        piClassesDir = Path(getKeyItem("piClassGCDir", "piClasses"))
        class_files = find_python_files_recursively(piClassesDir, "class")
        
        printIt(f"Found {len(class_files)} Python class files in {piClassesDir}", lable.INFO)
        
        for pyFile, file_type in class_files:
            if file_type == "class":
                className = pyFile.stem
                piSeedFile = findPiClassGCSeedFile(className)
                
                if piSeedFile:
                    changes = syncPythonClassToSeed(pyFile, piSeedFile)
                    if changes:
                        totalChanges += len(changes)
                        printIt(f"Synced {len(changes)} changes from {pyFile.relative_to(piClassesDir)}", lable.INFO)
                        for change in changes[:3]:  # Show first 3 changes
                            printIt(f"  • {change}", lable.DEBUG)
                        if len(changes) > 3:
                            printIt(f"  • ... and {len(changes) - 3} more", lable.DEBUG)
                    processedFiles += 1
                else:
                    printIt(f"No piSeed found for {className} ({pyFile.relative_to(piClassesDir)})", lable.DEBUG)
                    skippedFiles += 1
        
        # Process piDefGCDir recursively  
        piDefsDir = Path(getKeyItem("piDefGCDir", "piDefs"))
        def_files = find_python_files_recursively(piDefsDir, "def")
        
        printIt(f"Found {len(def_files)} Python function files in {piDefsDir}", lable.INFO)
        
        for pyFile, file_type in def_files:
            if file_type == "def":
                defName = pyFile.stem
                piSeedFile = findPiDefGCSeedFile(defName)
                
                if piSeedFile:
                    changes = syncPythonDefToSeed(pyFile, piSeedFile)
                    if changes:
                        totalChanges += len(changes)
                        printIt(f"Synced {len(changes)} changes from {pyFile.relative_to(piDefsDir)}", lable.INFO)
                        for change in changes[:3]:  # Show first 3 changes
                            printIt(f"  • {change}", lable.DEBUG)
                        if len(changes) > 3:
                            printIt(f"  • ... and {len(changes) - 3} more", lable.DEBUG)
                    processedFiles += 1
                else:
                    printIt(f"No piSeed found for {defName} ({pyFile.relative_to(piDefsDir)})", lable.DEBUG)
                    skippedFiles += 1
        
        # Summary report
        if processedFiles == 0 and skippedFiles == 0:
            printIt(f"No Python files found in {piClassesDir} or {piDefsDir} directories", lable.WARN)
        else:
            printIt(f"Summary: Processed {processedFiles} files, skipped {skippedFiles} files, made {totalChanges} total changes", lable.INFO)
            if skippedFiles > 0:
                printIt(f"Tip: Use 'piGenCode syncCode --create-missing' to auto-create piSeed files for orphaned Python files", lable.INFO)
        
    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'syncAllChangedFilesEnhanced error:\n{tb_str}', lable.ERROR)

def enhanced_file_discovery(fileName: str) -> Optional[Path]:
    """
    Enhanced file discovery that searches recursively in configured directories
    and handles various file naming patterns.
    """
    search_paths = []
    
    # Add configured directories
    piClassesDir = Path(getKeyItem("piClassGCDir", "piClasses"))
    piDefsDir = Path(getKeyItem("piDefGCDir", "piDefs"))
    
    if piClassesDir.exists():
        search_paths.append(piClassesDir)
    if piDefsDir.exists():
        search_paths.append(piDefsDir)
    
    # Add current directory as fallback
    search_paths.append(Path.cwd())
    
    # Try different file name variations
    name_variations = [
        fileName,
        f"{fileName}.py",
        fileName.replace(".py", ""),
    ]
    
    # Search in all paths
    for search_path in search_paths:
        for name_var in name_variations:
            # Direct match
            candidate = search_path / name_var
            if candidate.exists() and candidate.is_file():
                return candidate
            
            # Recursive search
            for py_file in search_path.rglob(name_var):
                if py_file.is_file() and py_file.suffix == '.py':
                    return py_file
    
    return None

def validate_sync_results(pythonFile: Path, piSeedFile: Path, changes: List[str]) -> bool:
    """
    Validate that sync results are reasonable and provide warnings for potential issues.
    """
    if not changes:
        return True
    
    # Check for suspicious patterns
    warnings = []
    
    # Check if too many changes (might indicate a problem)
    if len(changes) > 20:
        warnings.append(f"Large number of changes ({len(changes)}) - please review carefully")
    
    # Check for critical method changes
    critical_changes = [c for c in changes if any(critical in c.lower() for critical in ['__init__', 'json', '__str__'])]
    if critical_changes:
        warnings.append(f"Critical method changes detected: {', '.join(critical_changes)}")
    
    # Check file sizes for reasonableness
    try:
        py_size = pythonFile.stat().st_size
        seed_size = piSeedFile.stat().st_size
        
        if seed_size > py_size * 3:  # Seed file much larger than Python file
            warnings.append("piSeed file is significantly larger than Python file - possible duplication")
        
    except Exception:
        pass
    
    # Report warnings
    for warning in warnings:
        printIt(f"VALIDATION WARNING: {warning}", lable.WARN)
    
    return len(warnings) == 0

# Performance improvements
def batch_process_files(files: List[Path], process_func, batch_size: int = 10) -> Dict[str, any]:
    """
    Process files in batches to improve performance and provide progress feedback.
    """
    results = {
        'processed': 0,
        'changes': 0,
        'errors': 0,
        'skipped': 0
    }
    
    total_files = len(files)
    
    for i in range(0, total_files, batch_size):
        batch = files[i:i + batch_size]
        batch_end = min(i + batch_size, total_files)
        
        printIt(f"Processing files {i+1}-{batch_end} of {total_files}...", lable.INFO)
        
        for file_path in batch:
            try:
                result = process_func(file_path)
                if result:
                    results['processed'] += 1
                    if isinstance(result, list):
                        results['changes'] += len(result)
                else:
                    results['skipped'] += 1
            except Exception as e:
                results['errors'] += 1
                printIt(f"Error processing {file_path}: {e}", lable.ERROR)
    
    return results
