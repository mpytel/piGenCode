import shutil
import os
from pathlib import Path
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable


def rmGC(argParse: ArgParse):
    """
    Remove generated directories: piGerms, piClasses, and piDefs.
    This command cleans up all generated files to allow for a fresh start.
    """
    try:
        # List of directories to remove
        directories_to_remove = ["piGerms", "piClasses", "piDefs"]
        removed_dirs = []
        not_found_dirs = []
        
        for dir_name in directories_to_remove:
            dir_path = Path(dir_name)
            
            if dir_path.exists() and dir_path.is_dir():
                try:
                    shutil.rmtree(dir_path)
                    removed_dirs.append(dir_name)
                    printIt(f"Removed directory: {dir_name}", lable.INFO)
                except Exception as e:
                    printIt(f"Error removing directory {dir_name}: {e}", lable.ERROR)
            else:
                not_found_dirs.append(dir_name)
                printIt(f"Directory not found: {dir_name}", lable.DEBUG)
        
        # Summary message
        if removed_dirs:
            printIt(f"Successfully removed {len(removed_dirs)} directories: {', '.join(removed_dirs)}", lable.INFO)
        
        if not_found_dirs:
            printIt(f"Directories not found (already clean): {', '.join(not_found_dirs)}", lable.DEBUG)
        
        if not removed_dirs and not not_found_dirs:
            printIt("No directories to remove", lable.INFO)
        
        printIt("Clean-up complete. Ready for fresh generation.", lable.INFO)
        
    except Exception as e:
        printIt(f"Error in rmGC command: {e}", lable.ERROR)
