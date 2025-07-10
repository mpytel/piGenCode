import shutil
import os
from pathlib import Path
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..defs.piRCFile import getKeyItem


def rmGC(argParse: ArgParse):
    """
    Remove generated files to clean up for a fresh start.
    - piGerms (piScratchDir): Removes entire directory (volatile temp files)
    - piClasses (piClassGCDir): Recursively searches for .piclass tracking files and removes tracked files
    - piDefs (piDefGCDir): Recursively searches for .pidefs tracking files and removes tracked files
    
    This approach supports distributed file placement via fileDirectory and preserves user files.
    Empty directories are removed after cleanup.
    """
    try:
        removed_files = []
        removed_dirs = []
        not_found_items = []
        preserved_files = []

        # 1. Handle piGerms (piScratchDir) - Remove entire directory (volatile)
        piGermsDir = Path(getKeyItem("piScratchDir", "piGerms"))
        if piGermsDir.exists() and piGermsDir.is_dir():
            try:
                shutil.rmtree(piGermsDir)
                removed_dirs.append(f"piGerms ({piGermsDir})")
                printIt(f"Removed directory: piGerms ({piGermsDir})", lable.INFO)
            except Exception as e:
                printIt(f"Error removing directory piGerms ({piGermsDir}): {e}", lable.ERROR)
        else:
            not_found_items.append(f"piGerms ({piGermsDir})")

        # 2. Handle piClasses (piClassGCDir) - Recursive search for .piclass files
        piClassesDir = Path(getKeyItem("piClassGCDir", "piClasses"))
        removed_count, preserved_count, tracking_files_found = removeTrackedFilesRecursive(
            piClassesDir, ".piclass", "piClasses"
        )
        if removed_count > 0:
            removed_files.append(f"{removed_count} piClass files from {tracking_files_found} locations under {piClassesDir}")
        if preserved_count > 0:
            preserved_files.append(f"{preserved_count} user files preserved under {piClassesDir}")

        # 3. Handle piDefs (piDefGCDir) - Recursive search for .pidefs files  
        piDefsDir = Path(getKeyItem("piDefGCDir", "piDefs"))
        removed_count, preserved_count, tracking_files_found = removeTrackedFilesRecursive(
            piDefsDir, ".pidefs", "piDefs"
        )
        if removed_count > 0:
            removed_files.append(f"{removed_count} piDef files from {tracking_files_found} locations under {piDefsDir}")
        if preserved_count > 0:
            preserved_files.append(f"{preserved_count} user files preserved under {piDefsDir}")

        # Summary reporting
        if removed_dirs:
            printIt(f"Removed directories:", lable.INFO)
            for dir_info in removed_dirs:
                printIt(f"  • {dir_info}", lable.INFO)

        if removed_files:
            printIt(f"Removed generated files:", lable.INFO)
            for file_info in removed_files:
                printIt(f"  • {file_info}", lable.INFO)

        if preserved_files:
            printIt(f"Preserved user files:", lable.INFO)
            for file_info in preserved_files:
                printIt(f"  • {file_info}", lable.INFO)

        if not_found_items:
            printIt(f"Items not found (already clean):", lable.DirNotFound)
            for item_info in not_found_items:
                printIt(f"  • {item_info}", lable.DirNotFound)

        if not removed_dirs and not removed_files:
            printIt("No generated files to remove", lable.INFO)

        printIt("Clean-up complete. Generated files removed, user files preserved.", lable.INFO)

    except Exception as e:
        printIt(f"Error in rmGC command: {e}", lable.ERROR)


def removeTrackedFilesRecursive(rootDirectory: Path, trackingFileName: str, displayName: str) -> tuple:
    """
    Recursively search for tracking files and remove tracked files throughout directory tree.
    If no tracking files are found in the configured directory, expand search to find
    files placed via custom fileDirectory paths.
    
    Args:
        rootDirectory: Root directory to search recursively
        trackingFileName: Name of tracking file (.piclass or .pidefs)
        displayName: Display name for logging
        
    Returns:
        tuple: (total_removed_count, total_preserved_count, tracking_files_found)
    """
    total_removed_count = 0
    total_preserved_count = 0
    tracking_files_found = 0
    
    tracking_files = []
    
    # First, try to find tracking files in the configured directory (if it exists)
    if rootDirectory.exists():
        tracking_files = list(rootDirectory.rglob(trackingFileName))
    else:
        printIt(f"Configured directory not found: {displayName} ({rootDirectory})", lable.DEBUG)
    
    # If no tracking files found in configured directory, expand search scope
    if not tracking_files:
        # Search from current working directory to catch custom fileDirectory placements
        expanded_search_root = Path.cwd()
        printIt(f"No tracking files found in configured {displayName} directory, expanding search scope", lable.DEBUG)
        
        # Find all tracking files of this type in the entire project
        all_tracking_files = list(expanded_search_root.rglob(trackingFileName))
        
        # Filter to only include tracking files that are relevant to this file type
        # by checking if they're in directories that could contain the expected files
        for tracking_file in all_tracking_files:
            # Skip tracking files that are clearly in the wrong configured directory
            # (e.g., don't process .piclass files when looking for piDef files)
            if trackingFileName == ".pidefs" and "piClasses" in str(tracking_file):
                continue
            if trackingFileName == ".piclass" and "piDefs" in str(tracking_file):
                continue
                
            tracking_files.append(tracking_file)
    
    if not tracking_files:
        # No tracking files found anywhere
        if rootDirectory.exists():
            # Count all Python files as preserved user files
            python_files = list(rootDirectory.rglob("*.py"))
            total_preserved_count = len(python_files)
            if total_preserved_count > 0:
                printIt(f"No tracking files found in {displayName} ({rootDirectory})", lable.INFO)
                printIt(f"Preserved {total_preserved_count} existing Python files", lable.INFO)
        else:
            printIt(f"No tracking files found for {displayName} anywhere in project", lable.INFO)
        return 0, total_preserved_count, 0
    
    tracking_files_found = len(tracking_files)
    printIt(f"Found {tracking_files_found} tracking files for {displayName}", lable.INFO)
    
    # Process each tracking file
    for tracking_file in tracking_files:
        directory = tracking_file.parent
        removed_count, preserved_count = removeTrackedFilesInDirectory(
            directory, tracking_file, displayName
        )
        total_removed_count += removed_count
        total_preserved_count += preserved_count
    
    return total_removed_count, total_preserved_count, tracking_files_found


def removeTrackedFilesInDirectory(directory: Path, trackingFile: Path, displayName: str) -> tuple:
    """
    Remove tracked files in a specific directory based on its tracking file.
    If directory becomes empty after cleanup, remove the directory as well.
    
    Args:
        directory: Directory containing files and tracking file
        trackingFile: Path to the tracking file
        displayName: Display name for logging
        
    Returns:
        tuple: (removed_count, preserved_count)
    """
    removed_count = 0
    preserved_count = 0
    
    printIt(f"Processing tracking file: {trackingFile}", lable.DEBUG)
    
    # Read tracking file to get list of generated files
    try:
        with open(trackingFile, 'r') as f:
            # Skip comment lines starting with #
            tracked_files = set(line.strip() for line in f if line.strip() and not line.strip().startswith('#'))
    except Exception as e:
        printIt(f"Error reading tracking file {trackingFile}: {e}", lable.ERROR)
        return 0, 0
    
    # Get all Python files in this specific directory (not recursive)
    all_python_files = set(f.name for f in directory.glob("*.py"))
    
    # Remove tracked files
    for filename in tracked_files:
        file_path = directory / filename
        if file_path.exists():
            try:
                file_path.unlink()
                removed_count += 1
                printIt(f"Removed generated file: {file_path}", lable.DEBUG)
            except Exception as e:
                printIt(f"Error removing file {file_path}: {e}", lable.ERROR)
        else:
            printIt(f"Tracked file not found: {file_path}", lable.DEBUG)
    
    # Count preserved files (Python files not in tracking list)
    preserved_files = all_python_files - tracked_files
    preserved_count = len(preserved_files)
    
    if preserved_count > 0:
        printIt(f"Preserved {preserved_count} user files in {directory}", lable.DEBUG)
    
    # Remove tracking file itself
    try:
        trackingFile.unlink()
        printIt(f"Removed tracking file: {trackingFile}", lable.DEBUG)
    except Exception as e:
        printIt(f"Error removing tracking file {trackingFile}: {e}", lable.ERROR)
    
    # Check if directory is empty after cleanup and remove if so
    try:
        # Get all remaining files and directories in the directory
        remaining_items = list(directory.iterdir())
        
        if not remaining_items:
            # Directory is completely empty, remove it
            directory.rmdir()
            printIt(f"Removed empty directory: {directory}", lable.DEBUG)
        else:
            # Check if only hidden files or __pycache__ remain
            significant_items = [
                item for item in remaining_items 
                if not item.name.startswith('.') and item.name != '__pycache__'
            ]
            
            if not significant_items:
                # Only hidden files or __pycache__ remain, consider removing
                # But be conservative - only remove __pycache__ directories
                for item in remaining_items:
                    if item.name == '__pycache__' and item.is_dir():
                        try:
                            import shutil
                            shutil.rmtree(item)
                            printIt(f"Removed __pycache__ directory: {item}", lable.DEBUG)
                        except Exception as e:
                            printIt(f"Could not remove __pycache__ directory {item}: {e}", lable.DEBUG)
                
                # Check again if directory is now empty
                remaining_items = list(directory.iterdir())
                if not remaining_items:
                    directory.rmdir()
                    printIt(f"Removed empty directory: {directory}", lable.DEBUG)
                
    except Exception as e:
        printIt(f"Could not check/remove directory {directory}: {e}", lable.DEBUG)
    
    return removed_count, preserved_count
