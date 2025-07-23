import shutil
import os
from pathlib import Path
from pigencode.classes.argParse import ArgParse
from pigencode.defs.logIt import printIt, lable
from pigencode.defs.fileIO import getKeyItem, piGCDirs

# Global variable to track empty directories removed
empty_dirs_removed = []

def rmGC(argParse: ArgParse):
    """
    Remove generated files to clean up for a fresh start.
    - piGerms (piGermDir): Removes entire directory (volatile temp files)
    - piClasses (piClassGCDir): Recursively searches for .piclass tracking files and removes tracked files
    - piDefs (piDefGCDir): Recursively searches for .pidefs tracking files and removes tracked files

    This approach supports distributed file placement via fileDirectory and preserves user files.
    Empty directories are removed after cleanup, including parent directories that become empty.
    """
    try:
        print()
        removed_files = []
        removed_dirs = []
        not_found_items = []
        preserved_files = []

        # Reset global tracking of empty directories
        global empty_dirs_removed
        empty_dirs_removed = []

        # 1. Handle piGerms (piGermDir) - Remove entire directory (volatile)
        piGermsDir = Path(getKeyItem(piGCDirs[1]))
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
        piClassesDir = Path(getKeyItem(piGCDirs[1]))
        removed_count, preserved_count, tracking_files_found = removeTrackedFilesRecursive(
            piClassesDir, ".piclass", "piClasses"
        )
        if removed_count > 0:
            removed_files.append(f"{removed_count} piClass files from {tracking_files_found} locations under {piClassesDir}")
        if preserved_count > 0:
            preserved_files.append(f"{preserved_count} user files preserved under {piClassesDir}")

        # 3. Handle piDefs (piDefGCDir) - Recursive search for .pidefs files
        piDefsDir = Path(getKeyItem(piGCDirs[1]))
        removed_count, preserved_count, tracking_files_found = removeTrackedFilesRecursive(
            piDefsDir, ".pidefs", "piDefs"
        )
        if removed_count > 0:
            removed_files.append(f"{removed_count} piDef files from {tracking_files_found} locations under {piDefsDir}")
        if preserved_count > 0:
            preserved_files.append(f"{preserved_count} user files preserved under {piDefsDir}")

        # 4. Handle piSeeds (piSeedsDir) - Remove entire directory (volatile)
        piSeedsDir = Path(getKeyItem(piGCDirs[0]))
        if piSeedsDir.exists() and piSeedsDir.is_dir():
            try:
                shutil.rmtree(piSeedsDir)
                removed_dirs.append(f"piSeeds ({piSeedsDir})")
                printIt(
                    f"Removed directory: piSeeds ({piSeedsDir})", lable.INFO)
            except Exception as e:
                printIt(
                    f"Error removing directory piSeeds ({piSeedsDir}): {e}", lable.ERROR)
        else:
            not_found_items.append(f"piSeeds ({piSeedsDir})")

        # Summary reporting
        if removed_dirs:
            printIt(f"Removed directories:", lable.INFO)
            for dir_info in removed_dirs:
                printIt(f"  • {dir_info}", lable.INFO)

        if removed_files:
            printIt(f"Removed generated files:", lable.INFO)
            for file_info in removed_files:
                printIt(f"  • {file_info}", lable.INFO)

        if empty_dirs_removed:
            printIt(f"Removed empty directories:", lable.INFO)
            for dir_info in empty_dirs_removed:
                printIt(f"  • {dir_info}", lable.INFO)

        if preserved_files:
            printIt(f"Preserved user files:", lable.INFO)
            for file_info in preserved_files:
                printIt(f"  • {file_info}", lable.INFO)

        if not_found_items:
            for item_info in not_found_items:
                printIt(f"  • {item_info}", lable.DirNotFound)

        if not removed_dirs and not removed_files and not empty_dirs_removed:
            printIt("No generated files to remove", lable.INFO)

        printIt("Clean-up complete. Generated files removed, user files preserved.", lable.INFO)
        print()

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
        pass

    # If no tracking files found in configured directory, expand search scope
    if not tracking_files:
        # Search from current working directory to catch custom fileDirectory placements
        expanded_search_root = Path.cwd()

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
    Then recursively check parent directories and remove them if they become empty.

    Args:
        directory: Directory containing files and tracking file
        trackingFile: Path to the tracking file
        displayName: Display name for logging

    Returns:
        tuple: (removed_count, preserved_count)
    """
    removed_count = 0
    preserved_count = 0

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
            except Exception as e:
                printIt(f"Error removing file {file_path}: {e}", lable.ERROR)
        else:
            printIt(f"Tracked file not found: {file_path}", lable.WARN)

    if removed_count > 0:
        printIt(f"Removed {removed_count} generated files from: {directory}", lable.INFO)

    # Count preserved files (Python files not in tracking list)
    preserved_files = all_python_files - tracked_files
    preserved_count = len(preserved_files)

    if preserved_count > 0:
        printIt(f"Preserved {preserved_count} user files in {directory}", lable.INFO)

    # Remove tracking file itself
    try:
        trackingFile.unlink()
    except Exception as e:
        printIt(f"Error removing tracking file {trackingFile}: {e}", lable.ERROR)

    # Now check if directory is empty and remove if so
    check_and_remove_directory(directory)

    return removed_count, preserved_count


def check_and_remove_directory(directory: Path):
    """
    Check if a directory is empty (or contains only __pycache__) and remove it if so.
    Then recursively check parent directories.

    Args:
        directory: Directory to check and potentially remove
    """
    global empty_dirs_removed

    # Skip if directory doesn't exist or is not a directory
    if not directory.exists() or not directory.is_dir():
        return

    # Skip certain directories that should never be removed
    if directory.name in ['.git', '.github', '.vscode', 'env', 'venv']:
        return

    # Skip the current working directory and its parents
    cwd = Path.cwd()
    if directory == cwd or directory in cwd.parents:
        return

    try:
        # First, check if directory is empty
        remaining_items = list(directory.iterdir())

        if not remaining_items:
            # Directory is completely empty, remove it
            parent_dir = directory.parent
            try:
                directory.rmdir()
                printIt(f"Removed empty directory: {directory}", lable.INFO)
                empty_dirs_removed.append(str(directory))

                # Recursively check parent
                check_and_remove_directory(parent_dir)
            except Exception as e:
                printIt(f"Could not remove empty directory {directory}: {e}", lable.DEBUG)
        else:
            # Check if only hidden files or __pycache__ remain
            significant_items = [
                item for item in remaining_items
                if not item.name.startswith('.') and item.name != '__pycache__'
            ]

            if not significant_items:
                # Only hidden files or __pycache__ remain
                # Remove __pycache__ directories
                for item in remaining_items:
                    if item.name == '__pycache__' and item.is_dir():
                        try:
                            shutil.rmtree(item)
                            printIt(f"Removed __pycache__ directory: {item}", lable.DEBUG)
                        except Exception as e:
                            printIt(f"Could not remove __pycache__ directory {item}: {e}", lable.DEBUG)

                # Check again if directory is now empty
                remaining_items = list(directory.iterdir())
                if not remaining_items:
                    parent_dir = directory.parent
                    try:
                        directory.rmdir()
                        printIt(f"Removed empty directory: {directory}", lable.INFO)
                        empty_dirs_removed.append(str(directory))

                        # Recursively check parent
                        check_and_remove_directory(parent_dir)
                    except Exception as e:
                        printIt(f"Could not remove empty directory {directory}: {e}", lable.DEBUG)
    except Exception as e:
        printIt(f"Could not check directory {directory}: {e}", lable.DEBUG)
