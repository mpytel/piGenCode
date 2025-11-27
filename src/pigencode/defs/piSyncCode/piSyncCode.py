import traceback
from pathlib import Path
from typing import Tuple  # , Dict, List, Optional, Set, Any
from ..logIt import printIt, label
from ..fileIO import getKeyItem, piGCDirs
from .piSyncCodeUtil import \
    enhancedFileDiscovery, \
    getDestDirForFile, \
    findExistingPiSeedFile, \
    determineOptimalPiSeedType, \
    validateSyncResults, \
    findPiGenClassSeedFile, \
    findPiDefGCSeedFile, \
    findPiClassGCSeedFile, \
    findPythonFilesRecursively
from .piSyncPythonClassToSeed import \
    createNewPiClassGCSeedFile, \
    syncPythonClassToSeed
from .piSyncPythonDefToSeed import createNewPiDefGCSeedFile
from .piSyncPythonGenClassToSeed import \
    createNewPiGenClassSeedFile, \
    syncPythonGenClassToSeed

global options
global devExept
devExept = True
global showDefNames
# showDefNames = label.ABORTPRT
# showDefNames = label.IMPORT
showDefNames = label.ABORTPRT
showDefNames01 = label.ABORTPRT
showDefNames02 = label.ABORTPRT
showDefNames03 = label.ABORTPRT
# Intelligent pattern detection functions

def syncSingleFile(fileName: str, options: dict):
    """Enhanced single file sync with piGenClass support and additional options"""
    printIt(f'syncSingleFile: {fileName}', showDefNames)
    try:
        # Use enhanced file discovery
        filePath = enhancedFileDiscovery(fileName)

        if not filePath:
            printIt(f"File not found: {fileName}", label.FileNotFound)
            return

        if not filePath.suffix == '.py':
            printIt(f"File must be a Python file: {fileName}", label.ERROR)
            return

        # Show what we found
        if options.get('stats', False):
            printIt(f"Found file: {filePath}", label.INFO)

        className = filePath.stem

        # if piSeed file doew not exist force create all piSeeds
        if not Path(getKeyItem(piGCDirs[0])).is_dir():
            options['create_piSeeds'] = True

        dest_dir = options.get('dest_dir')
        if dest_dir:
            dest_dir = getDestDirForFile(filePath, options)
        else:
            dest_dir = str(filePath.parent)

        # First, check for existing piSeed files of any type
        existingPiSeedFile, existingType = findExistingPiSeedFile(filePath, dest_dir)
        # print('existingPiSeedFile',existingType,f'findExistingPiSeedFile({filePath}, {dest_dir})')
        # print('existingPiSeedFile',existingPiSeedFile)
  
        if existingPiSeedFile:
            # Use existing piSeed file type
            file_type = existingType
            piSeedFile = existingPiSeedFile
            if options.get('stats', False):
                printIt(
                    f"Found existing {file_type} piSeed file: {piSeedFile.name}", label.DEBUG)
            # Try to find or create piSeed file based on optimal type
            if file_type == "piDefGC":
                if options.get('dry_run', False):
                    printIt(
                        f"DRY RUN: Would create new piDefGC piSeed file for: {className}", label.INFO)
                    return  # Don't actually create in dry-run mode
                else:
                    printIt(
                        f"Creating new piDefGC piSeed file for: {className}", label.INFO)
                    piSeedFile = createNewPiDefGCSeedFile(className, filePath, piSeedFile, dest_dir)
            elif file_type == "piGenClass":
                if options.get('dry_run', False):
                    printIt(
                        f"DRY RUN: Would create new piGenClass piSeed file for: {className}", label.INFO)
                    return  # Don't actually create in dry-run mode
                else:
                    printIt(
                        f"Creating new piGenClass piSeed file for: {className}", label.INFO)
                    piSeedFile = createNewPiGenClassSeedFile(className, filePath, piSeedFile, dest_dir)

            else:  # piClassGC
                if options.get('dry_run', False):
                    printIt(
                        f"DRY RUN: Would create new piClassGC piSeed file for: {className}", label.INFO)
                    return  # Don't actually create in dry-run mode
                else:
                    printIt(
                        f"Creating new piClassGC piSeed file for: {className}", label.INFO)
                    piSeedFile = createNewPiClassGCSeedFile(className, filePath, piSeedFile, dest_dir)
            return
        else:
            # No existing piSeed file, determine optimal type
            file_type = determineOptimalPiSeedType(filePath)
            if options.get('stats', False):
                printIt(
                    f"No existing piSeed file found, detected optimal type: {file_type}", label.DEBUG)

            # Try to find or create piSeed file based on optimal type
            if file_type == "piDefGC":
                piSeedFile = findPiDefGCSeedFile(filePath, dest_dir)
                if not piSeedFile and options.get('create_piSeeds', False):
                    if options.get('dry_run', False):
                        printIt(
                            f"DRY RUN: Would create new piDefGC piSeed file for: {className}", label.INFO)
                        return  # Don't actually create in dry-run mode
                    else:
                        printIt(
                            f"Creating new piDefGC piSeed file for: {className}", label.INFO)
                        piSeedFile = createNewPiDefGCSeedFile(
                            className, filePath, None, dest_dir)
            elif file_type == "piGenClass":
                piSeedFile = findPiGenClassSeedFile(filePath, dest_dir)
                print('piSeedFile', piSeedFile)

                if not piSeedFile and options.get('create_piSeeds', False):
                    if options.get('dry_run', False):
                        printIt(
                            f"DRY RUN: Would create new piGenClass piSeed file for: {className}", label.INFO)
                        return  # Don't actually create in dry-run mode
                    else:
                        printIt(
                            f"Creating new piGenClass piSeed file for: {className}", label.INFO)
                        piSeedFile = createNewPiGenClassSeedFile(
                            className, filePath, None, dest_dir)

            else:  # piClassGC
                piSeedFile = findPiClassGCSeedFile(filePath, dest_dir)
                if not piSeedFile and options.get('create_piSeeds', False):
                    if options.get('dry_run', False):
                        printIt(
                            f"DRY RUN: Would create new piClassGC piSeed file for: {className}", label.INFO)
                        return  # Don't actually create in dry-run mode
                    else:
                        printIt(
                            f"Creating new piClassGC piSeed file for: {className}", label.INFO)
                        print('seedContent01')
                piSeedFile = createNewPiClassGCSeedFile(className, filePath, None, dest_dir)
                return
            
        # Apply exclude pattern filter
        # Tuple[filePath, str, str]
        actual_type = determineOptimalPiSeedType(filePath)
        files_to_process: list[Tuple[Path, str, str]] = [
            (filePath, actual_type, actual_type)]
        if options.get('exclude_pattern'):
            import fnmatch
            pattern = options['exclude_pattern']
            files_to_process = [
                (f, t, d) for f, t, d in files_to_process
                if not fnmatch.fnmatch(f.name, pattern)
            ]

        printIt(f"Found {len(files_to_process)} files to process", label.INFO)

        if options.get('dry_run', False):
            printIt("DRY RUN MODE - No changes will be made", label.WARN)
            if options.get('create_piSeeds', False):
                # Only show files that actually need piSeed creation
                files_needing_piSeeds = []
                for filePath, file_type, dir_type in files_to_process:
                    className = filePath.stem
                    piSeedFile = None

                    # Use the same prioritized detection logic as actual sync
                    # First check for existing piSeed files (prioritized)
                    piSeedFile = findPiClassGCSeedFile(filePath, dest_dir)
                    if piSeedFile:
                        continue  # Has piClassGC piSeed

                    piSeedFile = findPiGenClassSeedFile(filePath, dest_dir)
                    if piSeedFile:
                        continue  # Has piGenClass piSeed

                piSeedFile = findPiDefGCSeedFile(filePath, dest_dir)
                if not piSeedFile and options.get('create_piSeeds', False):
                    if options.get('dry_run', False):
                        printIt(
                            f"DRY RUN: Would create new piDefGC piSeed file for: {className}", label.INFO)
                        return  # Don't actually create in dry-run mode
                    else:
                        printIt(
                            f"Creating new piDefGC piSeed file for: {className}", label.INFO)
                        piSeedFile = createNewPiDefGCSeedFile(
                            className, filePath, None, dest_dir)
            elif file_type == "piGenClass":
                piSeedFile = findPiGenClassSeedFile(filePath, dest_dir)
                if not piSeedFile and options.get('create_piSeeds', False):
                    if options.get('dry_run', False):
                        printIt(
                            f"DRY RUN: Would create new piGenClass piSeed file for: {className}", label.INFO)
                        return  # Don't actually create in dry-run mode
                    else:
                        printIt(
                            f"Creating new piGenClass piSeed file for: {className}", label.INFO)
                        piSeedFile = createNewPiGenClassSeedFile(
                            className, filePath, None, dest_dir)
            else:  # piClassGC
                # piSeedFile = findPiClassGCSeedFile(filePath, dest_dir)
                # if not piSeedFile and options.get('create_piSeeds', False):
                #     if options.get('dry_run', False):
                #         printIt(
                #             f"DRY RUN: Would create new piClassGC piSeed file for: {className}", label.INFO)
                #         return  # Don't actually create in dry-run mode
                #     else:
                #         printIt(
                #             f"Creating new piClassGC piSeed file for: {className}", label.INFO)
                piSeedFile = createNewPiClassGCSeedFile(className, filePath, None, dest_dir)

        # Apply filter if specified
        if options.get('filter_type'):
            filter_map = {'class': 'piClassGC',
                          'def': 'piDefGC', 'genclass': 'piGenClass'}
            if file_type != filter_map.get(options['filter_type']):
                if options.get('stats', False):
                    printIt(
                        f"Skipping {filePath.name} - doesn't match filter {options['filter_type']}", label.DEBUG)
                return

        # Apply exclude pattern if specified
        if options.get('exclude_pattern'):
            import fnmatch
            if fnmatch.fnmatch(filePath.name, options['exclude_pattern']):
                if options.get('stats', False):
                    printIt(
                        f"Skipping {filePath.name} - matches exclude pattern", label.DEBUG)
                return

        # Check if we have a piSeed file to work with
        if not piSeedFile:
            printIt(
                f"{file_type} piSeed file not found for: {className}", label.WARN)
            if not options.get('create_piSeeds', False):
                printIt(
                    "Use --create-piSeeds to auto-create piSeed file", label.INFO)
            return

        # Dry run check
        if options.get('dry_run', False):
            printIt(
                f"DRY RUN: Would sync {filePath.name} to {piSeedFile.name}", label.INFO)
            return

        # Sync based on the determined file type
        # changes = []
        # if existingPiSeedFile:
        #     if file_type == "piDefGC":
        #         changes = syncPythonDefToSeed(filePath, piSeedFile, dest_dir)
        #     elif file_type == "piGenClass":
        #         changes = syncPythonGenClassToSeed(filePath, piSeedFile)
        #     else:  # piClassGC
        #         changes = syncPythonClassToSeed(filePath, piSeedFile, options)

        # # Validate results if requested
        # if options.get('validate', False) and piSeedFile:
        #     validateSyncResults(filePath, piSeedFile, changes)

        # # Report results
        # if changes:
        #     printIt(
        #         f"01 Synced {len(changes)} changes from {filePath.name} to {piSeedFile.name}", label.INFO)
        #     if options.get('stats', False):
        #         for change in changes:
        #             printIt(f"  • {change}", label.DEBUG)
        # else:
        #     printIt(f"(SSF)No changes needed for {filePath}", label.INFO)

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(
                None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def syncSingleFile', label.ERROR)
        printIt(
            f"Error syncing {fileName}: {e}", label.ERROR)


def syncDirectory(directory: Path, options: dict):
    """directory sync with piGenClass support and filtering"""
    errors = 0
    try:
        printIt(f'syncDirectory: {str(directory)}', showDefNames)
        if not directory.exists() or not directory.is_dir():
            printIt(
                f"Directory not found or not a directory: {directory}", label.ERROR)
            return

        # Find all Python files in the directory recursively
        python_files: list[Path] = []
        for py_file in directory.rglob("*.py"):
            if py_file.is_file():
                python_files.append(py_file)

        if not python_files:
            printIt(
                f"No Python files found in directory: {directory}", label.INFO)
            return

        # Apply exclude file pattern filter
        if options.get('exclude_pattern'):
            import fnmatch
            pattern = options['exclude_pattern']
            python_files = [
                f for f in python_files if not fnmatch.fnmatch(f.name, pattern)]

        # printIt(f"Found {len(python_files)} Python files in {directory}", label.INFO)
        if not Path(getKeyItem(piGCDirs[0])).is_dir():
            options['create_piSeeds'] = True

        if options.get('dry_run', False):

            printIt("DRY RUN MODE - No changes will be made", label.WARN)

            if options.get('create_piSeeds', False):
                # Only show files that actually need piSeed creation
                files_needing_piSeeds = []
                for py_file in python_files:
                    # syncSingleFile(str(py_file), options)
                    className = py_file.stem
                    piSeedFile = None

                    dest_dir = options.get('dest_dir')
                    if dest_dir:
                        dest_dir = getDestDirForFile(py_file, options)
                    # Use the same prioritized detection logic as actual sync
                    # First check for existing piSeed files (prioritized)
                    piSeedFile = findPiClassGCSeedFile(py_file, dest_dir)
                    if piSeedFile:
                        continue  # Has piClassGC piSeed

                    piSeedFile = findPiGenClassSeedFile(py_file, dest_dir)
                    if piSeedFile:
                        continue  # Has piGenClass piSeed

                    piSeedFile = findPiDefGCSeedFile(py_file, dest_dir)
                    if piSeedFile:
                        continue  # Has piDefGC piSeed

                    # No existing piSeed found, determine optimal type
                    optimal_type = determineOptimalPiSeedType(py_file)

                    # Apply filter if specified
                    if options.get('filter_type'):
                        filter_map = {'class': 'piClassGC',
                                      'def': 'piDefGC', 'genclass': 'piGenClass'}
                        if optimal_type != filter_map.get(options['filter_type']):
                            continue  # Skip files that don't match filter

                    files_needing_piSeeds.append((py_file, optimal_type))

                if files_needing_piSeeds:
                    printIt(
                        f"Found {len(files_needing_piSeeds)} files that need piSeed creation:", label.INFO)
                    # Show first 10
                    for py_file, file_type in files_needing_piSeeds[:10]:
                        printIt(
                            f"  Would create {file_type} piSeed for: {py_file.name}", label.DEBUG)
                    if len(files_needing_piSeeds) > 10:
                        printIt(
                            f"  ... and {len(files_needing_piSeeds) - 10} more files", label.DEBUG)
                else:
                    printIt("No files found that need piSeed creation", label.INFO)
            else:
                # Show regular sync operations
                for py_file in python_files[:10]:  # Show first 10
                    file_type = determineOptimalPiSeedType(py_file)
                    printIt(
                        f"  Would process: {py_file.name} ({file_type})", label.DEBUG)
                if len(python_files) > 10:
                    printIt(
                        f"  ... and {len(python_files) - 10} more files", label.DEBUG)
            return

        # Process each file
        totalChanges = 0
        processedFiles = 0
        skippedFiles = 0
        createdSeeds = 0

        for py_file in python_files:
            defName = py_file.stem
            try:
                dest_dir = options.get('dest_dir')
                if dest_dir:
                    dest_dir = getDestDirForFile(py_file, options)
                # Determine file type
                file_type = determineOptimalPiSeedType(py_file)
                # Apply filter if specified
                if options.get('filter_type'):
                    filter_map = {'class': 'piClassGC',
                                  'def': 'piDefGC', 'genclass': 'piGenClass'}
                    if file_type != filter_map.get(options['filter_type']):
                        if options.get('stats', False):
                            printIt(
                                f"Skipping {py_file.name} - doesn't match filter", label.DEBUG)
                        continue

                # here is where one file is processed
                # Process based on type
                changes = []
                piSeedFile = None

                if file_type == "piDefGC":
                    piSeedFile = findPiDefGCSeedFile(py_file, dest_dir)
                    if piSeedFile:
                        piSeedFile = createNewPiDefGCSeedFile(defName, py_file, piSeedFile, dest_dir)
                    else:
                        piSeedFile = createNewPiDefGCSeedFile(defName, py_file, None, dest_dir)
                    if piSeedFile:
                        createdSeeds += 1

                elif file_type == "piGenClass":
                    className = py_file.stem
                    piSeedFile = findPiGenClassSeedFile(py_file, dest_dir)
                    if piSeedFile:
                        piSeedFile = createNewPiGenClassSeedFile(className, py_file, piSeedFile, dest_dir)
                    else:
                        piSeedFile = createNewPiGenClassSeedFile(className, py_file, None, dest_dir)
                    if piSeedFile:
                        createdSeeds += 1
                else:  # piClassGC
                    className = py_file.stem
                    piSeedFile = findPiClassGCSeedFile(py_file)
                    if piSeedFile:
                        piSeedFile = createNewPiClassGCSeedFile(className, py_file, piSeedFile, dest_dir)
                    else:
                        piSeedFile = createNewPiClassGCSeedFile(className, py_file, None, dest_dir)
                    if piSeedFile:
                        createdSeeds += 1

                # Validate results if requested
                if options.get('validate', False) and piSeedFile:
                    validateSyncResults(py_file, piSeedFile, changes)

                # Track results
                if changes:
                    # for change in changes:
                    #     print(change)
                    totalChanges += len(changes)
                    if options.get('stats', False):
                        printIt(
                            f"04 Synced {len(changes)} changes from {py_file.name}", label.INFO)
                    processedFiles += 1
                elif piSeedFile:
                    processedFiles += 1
                else:
                    skippedFiles += 1

            except Exception as e:
                lineNum = f"{e.__traceback__.tb_lineno})" if e.__traceback__ is not None else ""
                printIt(
                    f"Error processing {py_file}: {e} {lineNum}", label.ERROR)
                errors += 1

        # Final summary
        printIt(f"Directory Sync Complete:", label.INFO)
        printIt(f"  • Processed: {processedFiles} files", label.BLANK)
        printIt(f"  • Changes made: {totalChanges}", label.BLANK)
        printIt(f"  • Skipped: {skippedFiles} files", label.BLANK)
        if createdSeeds > 0:
            printIt(f"  • Created piSeed files: {createdSeeds}", label.BLANK)

        # if skippedFiles > 0 and not options.get('create_piSeeds', False):
        #     printIt("Tip: Use --create-piSeeds to auto-create piSeed files for orphaned Python files", label.INFO)

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(
                None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def syncDirectory', label.ERROR)
        printIt(
            f"Error syncing directory {directory}: {e}", label.ERROR)
        errors += 1

    if errors > 0:
        printIt(f"  • Errors: {errors}", label.BLANK)

def syncAllFiles(options: dict):
    """sync all files with piGenClass support, filtering and advanced options"""
    printIt('syncAllFiles', showDefNames)
    try:
        totalChanges = 0
        processedFiles = 0
        skippedFiles = 0
        createdSeeds = 0

        # Collect all files to process
        files_to_process: list[Tuple[Path, str, str]] = []

        # Process piClassGCDir if not filtered to def/genclass only
        if options.get('filter_type') not in ['def', 'genclass']:
            piClassesDir = Path(getKeyItem(piGCDirs[2]))
            if piClassesDir.exists():
                class_files = findPythonFilesRecursively(piClassesDir, "class")
                files_to_process.extend([(f, t, 'class')
                                        for f, t in class_files])

        # Process piDefGCDir if not filtered to class/genclass only
        if options.get('filter_type') not in ['class', 'genclass']:
            piDefsDir = Path(getKeyItem(piGCDirs[3]))
            if piDefsDir.exists():
                def_files = findPythonFilesRecursively(piDefsDir, "def")
                files_to_process.extend([(f, t, 'def') for f, t in def_files])

        # Process piGenClassDir if not filtered to class/def only
        if options.get('filter_type') not in ['class', 'def']:
            # piGenClass files can be in either piClassGCDir or a separate directory
            # Check both locations
            piGenClassDirs = [
                Path(getKeyItem(piGCDirs[4])),
                Path(getKeyItem(piGCDirs[3]))
            ]

            for genClassDir in piGenClassDirs:
                if genClassDir.exists():
                    genclass_files = findPythonFilesRecursively(
                        genClassDir, "genclass")
                    files_to_process.extend(
                        [(f, t, 'genclass') for f, t in genclass_files])

        # Remove duplicates (files might be found in multiple directories)
        unique_files = {}
        for filePath, file_type, dir_type in files_to_process:
            key = str(filePath.resolve())
            if key not in unique_files:
                unique_files[key] = (filePath, file_type, dir_type)

        files_to_process = list(unique_files.values())

        # Apply exclude pattern filter
        if options.get('exclude_pattern'):
            import fnmatch
            pattern = options['exclude_pattern']
            files_to_process = [
                (f, t, d) for f, t, d in files_to_process
                if not fnmatch.fnmatch(f.name, pattern)
            ]

        printIt(f"Found {len(files_to_process)} files to process", label.INFO)

        if options.get('dry_run', False):
            printIt("DRY RUN MODE - No changes will be made", label.WARN)

            if options.get('create_piSeeds', False):
                # Only show files that actually need piSeed creation
                files_needing_piSeeds = []
                for filePath, file_type, dir_type in files_to_process:
                    className = filePath.stem
                    piSeedFile = None
                    dest_dir = options.get('dest_dir')
                    if dest_dir:
                        dest_dir = getDestDirForFile(filePath, options)

                    # Use the same prioritized detection logic as actual sync
                    # First check for existing piSeed files (prioritized)
                    piSeedFile = findPiClassGCSeedFile(filePath, dest_dir)
                    if piSeedFile:
                        continue  # Has piClassGC piSeed

                    piSeedFile = findPiGenClassSeedFile(filePath, dest_dir)
                    if piSeedFile:
                        continue  # Has piGenClass piSeed

                    piSeedFile = findPiDefGCSeedFile(
                        filePath, dest_dir)
                    if piSeedFile:
                        continue  # Has piDefGC piSeed

                    # No existing piSeed found, determine optimal type
                    optimal_type = determineOptimalPiSeedType(filePath)

                    # Apply filter if specified
                    if options.get('filter_type'):
                        filter_map = {'class': 'piClassGC',
                                      'def': 'piDefGC', 'genclass': 'piGenClass'}
                        if optimal_type != filter_map.get(options['filter_type']):
                            continue  # Skip files that don't match filter

                    files_needing_piSeeds.append((filePath, optimal_type))

                if files_needing_piSeeds:
                    printIt(
                        f"Found {len(files_needing_piSeeds)} files that need piSeed creation:", label.INFO)
                    # Show first 10
                    for filePath, file_type in files_needing_piSeeds[:10]:
                        printIt(
                            f"  Would create {file_type} piSeed for: {filePath.name}", label.DEBUG)
                    if len(files_needing_piSeeds) > 10:
                        printIt(
                            f"  ... and {len(files_needing_piSeeds) - 10} more files", label.DEBUG)
                else:
                    printIt("No files found that need piSeed creation", label.INFO)
            else:
                # Show regular sync operations
                # Show first 10
                for filePath, file_type, dir_type in files_to_process[:10]:
                    printIt(
                        f"  Would process: {filePath.name} ({file_type})", label.DEBUG)
                if len(files_to_process) > 10:
                    printIt(
                        f"  ... and {len(files_to_process) - 10} more files", label.DEBUG)
            return

        # Process files
        for filePath, file_type, dir_type in files_to_process:
            try:

                dest_dir = options.get('dest_dir')
                if dest_dir:
                    dest_dir = getDestDirForFile(filePath, options)
                # Determine optimal piSeed type for each file
                optimal_type = determineOptimalPiSeedType(filePath)

                if optimal_type == "piDefGC":
                    defName = filePath.stem
                    piSeedFile = findPiDefGCSeedFile(filePath, dest_dir)
                    if piSeedFile and options.get('create_piSeeds', True):
                        changes = syncPythonDefToSeed(
                            filePath, piSeedFile, dest_dir)
                        if changes:
                            totalChanges += len(changes)
                            if options.get('stats', False):
                                printIt(
                                    f"02 Synced {len(changes)} changes from {filePath.name}", label.INFO)
                        processedFiles += 1
                    else:
                        piSeedFile = createNewPiDefGCSeedFile(
                            defName, filePath, None, dest_dir)
                        if piSeedFile:
                            createdSeeds += 1
                        else:
                            skippedFiles += 1

                elif optimal_type == "piGenClass":
                    className = filePath.stem
                    piSeedFile = findPiGenClassSeedFile(filePath, dest_dir)
                    if piSeedFile and options.get('create_piSeeds', True):
                        changes = createNewPiGenClassSeedFile(className, filePath, piSeedFile, dest_dir)
                        if changes:
                            totalChanges += len(changes)
                            if options.get('stats', False):
                                printIt(
                                    f"03 Synced {len(changes)} changes from {filePath.name}", label.INFO)
                        processedFiles += 1
                    else:
                        piSeedFile = createNewPiGenClassSeedFile(className, filePath, piSeedFile, dest_dir)
                        if piSeedFile:
                            createdSeeds += 1
                        else:
                            skippedFiles += 1

                else:  # piClassGC
                    className = filePath.stem
                    # piSeedFile = findPiClassGCSeedFile(filePath, dest_dir)
                    # if piSeedFile and options.get('create_piSeeds', True):
                    #     changes = syncPythonClassToSeed(
                    #         filePath, piSeedFile, options)
                    #     if changes:
                    #         totalChanges += len(changes)
                    #         if options.get('stats', False):
                    #             printIt(
                    #                 f"04.1 Synced {len(changes)} changes from {filePath.name}", label.INFO)
                    #     processedFiles += 1
                    # else:
                    piSeedFile = createNewPiClassGCSeedFile(className, filePath, None, dest_dir)
                    if piSeedFile:
                        createdSeeds += 1
                    else:
                        skippedFiles += 1

            except Exception as e:
                lineNum = f"{e.__traceback__.tb_lineno})" if e.__traceback__ is not None else ""
                printIt(
                    f"Error processing {filePath}: {e} {lineNum}", label.ERROR)
                skippedFiles += 1

        # Final summary
        printIt(f"Sync Complete:", label.INFO)
        printIt(f"  • Processed: {processedFiles} files", label.INFO)
        printIt(f"  • Changes made: {totalChanges}", label.INFO)
        printIt(f"  • Skipped: {skippedFiles} files", label.INFO)
        if createdSeeds > 0:
            printIt(f"  • Created piSeed files: {createdSeeds}", label.INFO)

        if skippedFiles > 0 and not options.get('create_piSeeds', False):
            printIt(
                "Tip: Use --create-piSeeds to auto-create piSeed files for orphaned Python files", label.INFO)

    except Exception as e:
        if devExept:
            tb_str = ''.join(traceback.format_exception(
                None, e, e.__traceback__))
            printIt(f'{tb_str}\n\n --- def syncAllFiles', label.ERROR)
        printIt(
            f"Error syncing all files: {e}", label.ERROR)
