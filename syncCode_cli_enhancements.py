# Enhanced CLI interface for syncCode command

def syncCodeEnhanced(argParse: ArgParse):
    """
    Enhanced syncCode with additional command line options and better user experience.
    
    New usage patterns:
    piGenCode syncCode                           # Sync all files (existing behavior)
    piGenCode syncCode <filename>                # Sync specific file (existing behavior)
    piGenCode syncCode --recursive               # Force recursive scanning
    piGenCode syncCode --dry-run                # Show what would be changed without making changes
    piGenCode syncCode --create-missing          # Auto-create piSeed files for orphaned Python files
    piGenCode syncCode --validate                # Validate sync results
    piGenCode syncCode --stats                   # Show detailed statistics
    piGenCode syncCode --filter class           # Only sync class files
    piGenCode syncCode --filter def             # Only sync function definition files
    piGenCode syncCode --exclude-pattern "test_*" # Exclude files matching pattern
    piGenCode syncCode --force                   # Force sync even for default patterns
    """
    
    args = argParse.parser.parse_args()
    theArgs = args.arguments
    
    # Parse command line options
    options = {
        'dry_run': '--dry-run' in theArgs,
        'recursive': '--recursive' in theArgs,
        'create_missing': '--create-missing' in theArgs,
        'validate': '--validate' in theArgs,
        'stats': '--stats' in theArgs,
        'force': '--force' in theArgs,
        'filter_type': None,
        'exclude_pattern': None,
        'target_file': None
    }
    
    # Extract filter type
    if '--filter' in theArgs:
        filter_idx = theArgs.index('--filter')
        if filter_idx + 1 < len(theArgs):
            filter_type = theArgs[filter_idx + 1]
            if filter_type in ['class', 'def']:
                options['filter_type'] = filter_type
    
    # Extract exclude pattern
    if '--exclude-pattern' in theArgs:
        pattern_idx = theArgs.index('--exclude-pattern')
        if pattern_idx + 1 < len(theArgs):
            options['exclude_pattern'] = theArgs[pattern_idx + 1]
    
    # Extract target file (non-option arguments)
    non_option_args = [arg for arg in theArgs if not arg.startswith('--')]
    if non_option_args:
        options['target_file'] = non_option_args[0]
    
    # Show options if stats requested
    if options['stats']:
        printIt("syncCode Enhanced Options:", lable.INFO)
        for key, value in options.items():
            if value is not None and value is not False:
                printIt(f"  {key}: {value}", lable.DEBUG)
    
    # Execute based on options
    if options['target_file']:
        # Sync specific file
        syncSingleFileEnhanced(options['target_file'], options)
    else:
        # Sync all files
        syncAllFilesEnhanced(options)

def syncSingleFileEnhanced(fileName: str, options: dict):
    """Enhanced single file sync with additional options"""
    try:
        # Use enhanced file discovery
        filePath = enhanced_file_discovery(fileName)
        
        if not filePath:
            printIt(f"File not found: {fileName}", lable.FileNotFound)
            return
        
        if not filePath.suffix == '.py':
            printIt(f"File must be a Python file: {fileName}", lable.ERROR)
            return
        
        # Show what we found
        printIt(f"Found file: {filePath}", lable.INFO)
        
        # Determine file type
        isDefFile = isPythonFileDefType(filePath)
        file_type = "piDefGC" if isDefFile else "piClassGC"
        
        printIt(f"Detected file type: {file_type}", lable.DEBUG)
        
        # Find or create piSeed file
        if isDefFile:
            defName = filePath.stem
            piSeedFile = findPiDefGCSeedFile(defName)
            
            if not piSeedFile and options.get('create_missing', False):
                printIt(f"Creating new piDefGC piSeed file for: {defName}", lable.INFO)
                piSeedFile = createNewPiDefGCSeedFile(defName, filePath)
            
            if not piSeedFile:
                printIt(f"piDefGC piSeed file not found for: {defName}", lable.WARN)
                printIt("Use --create-missing to auto-create piSeed file", lable.INFO)
                return
            
            # Dry run check
            if options.get('dry_run', False):
                printIt(f"DRY RUN: Would sync {filePath.name} to {piSeedFile.name}", lable.INFO)
                return
            
            changes = syncPythonDefToSeed(filePath, piSeedFile)
        else:
            className = filePath.stem
            piSeedFile = findPiClassGCSeedFile(className)
            
            if not piSeedFile and options.get('create_missing', False):
                printIt(f"Creating new piClassGC piSeed file for: {className}", lable.INFO)
                piSeedFile = createNewPiClassGCSeedFile(className, filePath)
            
            if not piSeedFile:
                printIt(f"piClassGC piSeed file not found for class: {className}", lable.WARN)
                printIt("Use --create-missing to auto-create piSeed file", lable.INFO)
                return
            
            # Dry run check
            if options.get('dry_run', False):
                printIt(f"DRY RUN: Would sync {filePath.name} to {piSeedFile.name}", lable.INFO)
                return
            
            changes = syncPythonClassToSeed(filePath, piSeedFile)
        
        # Validate results if requested
        if options.get('validate', False):
            validate_sync_results(filePath, piSeedFile, changes)
        
        # Report results
        if changes:
            printIt(f"Synced {len(changes)} changes from {filePath.name} to {piSeedFile.name}", lable.INFO)
            if options.get('stats', False):
                for change in changes:
                    printIt(f"  • {change}", lable.DEBUG)
        else:
            printIt(f"No changes needed for {filePath.name}", lable.INFO)
            
    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'syncSingleFileEnhanced error:\n{tb_str}', lable.ERROR)

def syncAllFilesEnhanced(options: dict):
    """Enhanced sync all files with filtering and advanced options"""
    try:
        totalChanges = 0
        processedFiles = 0
        skippedFiles = 0
        createdSeeds = 0
        
        # Collect all files to process
        files_to_process = []
        
        # Process piClassGCDir if not filtered to def only
        if options.get('filter_type') != 'def':
            piClassesDir = Path(getKeyItem("piClassGCDir", "piClasses"))
            if piClassesDir.exists():
                class_files = find_python_files_recursively(piClassesDir, "class")
                files_to_process.extend([(f, t, 'class') for f, t in class_files])
        
        # Process piDefGCDir if not filtered to class only
        if options.get('filter_type') != 'class':
            piDefsDir = Path(getKeyItem("piDefGCDir", "piDefs"))
            if piDefsDir.exists():
                def_files = find_python_files_recursively(piDefsDir, "def")
                files_to_process.extend([(f, t, 'def') for f, t in def_files])
        
        # Apply exclude pattern filter
        if options.get('exclude_pattern'):
            import fnmatch
            pattern = options['exclude_pattern']
            files_to_process = [
                (f, t, d) for f, t, d in files_to_process 
                if not fnmatch.fnmatch(f.name, pattern)
            ]
        
        printIt(f"Found {len(files_to_process)} files to process", lable.INFO)
        
        if options.get('dry_run', False):
            printIt("DRY RUN MODE - No changes will be made", lable.WARN)
            for filePath, file_type, dir_type in files_to_process[:10]:  # Show first 10
                printIt(f"  Would process: {filePath.name} ({file_type})", lable.DEBUG)
            if len(files_to_process) > 10:
                printIt(f"  ... and {len(files_to_process) - 10} more files", lable.DEBUG)
            return
        
        # Process files
        for filePath, file_type, dir_type in files_to_process:
            try:
                if file_type == "def":
                    defName = filePath.stem
                    piSeedFile = findPiDefGCSeedFile(defName)
                    
                    if not piSeedFile and options.get('create_missing', False):
                        piSeedFile = createNewPiDefGCSeedFile(defName, filePath)
                        if piSeedFile:
                            createdSeeds += 1
                    
                    if piSeedFile:
                        changes = syncPythonDefToSeed(filePath, piSeedFile)
                        if changes:
                            totalChanges += len(changes)
                            if options.get('stats', False):
                                printIt(f"Synced {len(changes)} changes from {filePath.name}", lable.INFO)
                        processedFiles += 1
                    else:
                        skippedFiles += 1
                        
                else:  # class file
                    className = filePath.stem
                    piSeedFile = findPiClassGCSeedFile(className)
                    
                    if not piSeedFile and options.get('create_missing', False):
                        piSeedFile = createNewPiClassGCSeedFile(className, filePath)
                        if piSeedFile:
                            createdSeeds += 1
                    
                    if piSeedFile:
                        changes = syncPythonClassToSeed(filePath, piSeedFile)
                        if changes:
                            totalChanges += len(changes)
                            if options.get('stats', False):
                                printIt(f"Synced {len(changes)} changes from {filePath.name}", lable.INFO)
                        processedFiles += 1
                    else:
                        skippedFiles += 1
                        
            except Exception as e:
                printIt(f"Error processing {filePath}: {e}", lable.ERROR)
                skippedFiles += 1
        
        # Final summary
        printIt(f"Sync Complete:", lable.INFO)
        printIt(f"  • Processed: {processedFiles} files", lable.INFO)
        printIt(f"  • Changes made: {totalChanges}", lable.INFO)
        printIt(f"  • Skipped: {skippedFiles} files", lable.INFO)
        if createdSeeds > 0:
            printIt(f"  • Created piSeed files: {createdSeeds}", lable.INFO)
        
        if skippedFiles > 0 and not options.get('create_missing', False):
            printIt("Tip: Use --create-missing to auto-create piSeed files for orphaned Python files", lable.INFO)
        
    except Exception as e:
        tb_str = ''.join(traceback.format_exception(None, e, e.__traceback__))
        printIt(f'syncAllFilesEnhanced error:\n{tb_str}', lable.ERROR)

# Help text for the enhanced syncCode command
SYNC_CODE_HELP = """
syncCode - Synchronize Python files back to piSeed definitions

USAGE:
    piGenCode syncCode [options] [filename]

OPTIONS:
    --dry-run           Show what would be changed without making changes
    --recursive         Force recursive directory scanning (default)
    --create-missing    Auto-create piSeed files for orphaned Python files
    --validate          Validate sync results and show warnings
    --stats             Show detailed statistics and change information
    --force             Force sync even for default/generated patterns
    --filter <type>     Only sync specific file types (class|def)
    --exclude-pattern   Exclude files matching glob pattern

EXAMPLES:
    piGenCode syncCode                          # Sync all files
    piGenCode syncCode MyClass.py               # Sync specific file
    piGenCode syncCode --dry-run                # Preview changes
    piGenCode syncCode --create-missing         # Create missing piSeed files
    piGenCode syncCode --filter class          # Only sync class files
    piGenCode syncCode --exclude-pattern "test_*"  # Skip test files
    piGenCode syncCode --stats --validate      # Detailed sync with validation

WORKFLOW:
    1. Modify generated Python files in piClasses/ or piDefs/
    2. Run syncCode to update corresponding piSeed files
    3. Use genCode to regenerate and verify changes
    4. Commit both Python and piSeed changes to version control
"""
