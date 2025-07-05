import os
import shutil
from pathlib import Path
from re import compile as reCompile
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, lable
from ..defs.piRCFile import getKeyItem, writeRC

# Pattern to match piSeed files: piSeed000_name.pi
seedFilePattern = reCompile(r'piSeed(\d{3})_(.+)\.pi')

def reorderSeeds(argParse: ArgParse):
    """
    Reorder piSeed files by moving one file to a new position and renumbering all affected files.
    
    Usage: 
        piGenCode reorderSeeds <source_file> <target_file>
        piGenCode reorderSeeds <source_number> <target_number>
    
    Examples:
        piGenCode reorderSeeds piSeeds/piSeed044_piStruct_piDefGC.pi piSeeds/piSeed009_piStruct_piDefGC.pi
        piGenCode reorderSeeds 44 9
    
    This will:
    1. Move piSeed044 to position 009
    2. Increment all files from 009-043 by 1 (009->010, 010->011, etc.)
    3. Maintain the same processing order for all other files
    """
    args = argParse.parser.parse_args()
    theArgs = args.arguments
    
    if len(theArgs) != 2:
        printIt("Usage: piGenCode reorderSeeds <source_file> <target_file>", lable.ERROR)
        printIt("   OR: piGenCode reorderSeeds <source_number> <target_number>", lable.ERROR)
        printIt("Examples:", lable.INFO)
        printIt("  piGenCode reorderSeeds piSeeds/piSeed044_piStruct_piDefGC.pi piSeeds/piSeed009_piStruct_piDefGC.pi", lable.INFO)
        printIt("  piGenCode reorderSeeds 44 9", lable.INFO)
        return
    
    # Get piSeeds directory first
    seeds_dir = getSeedPath()
    if not seeds_dir:
        printIt("Could not find piSeeds directory", lable.ERROR)
        return
    
    # Get all piSeed files for reference
    all_seed_files = getAllSeedFiles(seeds_dir)
    
    # Check if arguments are integers (shortcut mode) or file paths
    source_arg = theArgs[0]
    target_arg = theArgs[1]
    
    try:
        # Try to parse as integers
        source_num = int(source_arg)
        target_num = int(target_arg)
        
        # Integer shortcut mode - construct file paths
        if source_num not in all_seed_files:
            printIt(f"Source piSeed{source_num:03d} not found", lable.ERROR)
            return
        
        source_file_info = all_seed_files[source_num]
        source_file = str(source_file_info['path'])
        
        # For target, we need to construct the target filename
        # Use the same name as source but with target number
        target_name = source_file_info['name']
        target_file = f"piSeeds/piSeed{target_num:03d}_{target_name}.pi"
        
        printIt(f"Integer shortcut mode: {source_num} -> {target_num}", lable.INFO)
        
    except ValueError:
        # File path mode - use arguments as-is
        source_file = source_arg
        target_file = target_arg
        printIt("File path mode", lable.INFO)
    
    # Validate and parse file paths
    source_path = Path(source_file)
    target_path = Path(target_file)
    
    if not source_path.exists():
        printIt(f"Source file not found: {source_file}", lable.ERROR)
        return
    
    # Extract numbers from filenames
    source_match = seedFilePattern.match(source_path.name)
    target_match = seedFilePattern.match(target_path.name)
    
    if not source_match:
        printIt(f"Invalid source filename format: {source_path.name}", lable.ERROR)
        return
    
    if not target_match:
        printIt(f"Invalid target filename format: {target_path.name}", lable.ERROR)
        return
    
    source_num = int(source_match.group(1))
    target_num = int(target_match.group(1))
    source_name = source_match.group(2)
    target_name = target_match.group(2)
    
    printIt(f"Moving piSeed{source_num:03d} to position {target_num:03d}", lable.INFO)
    
    # Show preview of changes
    showPreview(all_seed_files, source_num, target_num)
    
    if source_num == target_num:
        printIt("Source and target positions are the same - no changes needed", lable.WARN)
        return
    
    # Perform the reordering
    if source_num > target_num:
        # Moving backwards (e.g., 044 -> 009)
        moveBackwards(seeds_dir, all_seed_files, source_num, target_num, source_name, target_name)
    else:
        # Moving forwards (e.g., 009 -> 044)  
        moveForwards(seeds_dir, all_seed_files, source_num, target_num, source_name, target_name)
    
    # Validate the reordering
    if validateReorder(seeds_dir):
        printIt(f"Successfully reordered piSeed files", lable.INFO)
    else:
        printIt(f"Reordering completed but validation found issues", lable.WARN)

def getSeedPath() -> Path:
    """Get the piSeeds directory path"""
    seedDirName = "piSeeds"
    seedPath = Path(getKeyItem("piSeedsDir", seedDirName))
    if seedPath.is_dir():
        return seedPath
    
    # Check current directory
    cwd = Path.cwd()
    if cwd.name == seedDirName:
        seedPath = cwd
    else:
        cwdDirs = [str(p.name) for p in cwd.iterdir() if p.is_dir()]
        if seedDirName in cwdDirs:
            seedPath = cwd.joinpath(seedDirName)
    
    if seedPath and seedPath.is_dir():
        writeRC("piSeedsDir", str(seedPath))
        return seedPath
    
    return None

def getAllSeedFiles(seeds_dir: Path) -> dict:
    """Get all piSeed files and their numbers"""
    seed_files = {}
    
    for file_path in seeds_dir.glob("piSeed*.pi"):
        match = seedFilePattern.match(file_path.name)
        if match:
            file_num = int(match.group(1))
            seed_files[file_num] = {
                'path': file_path,
                'name': match.group(2),
                'full_name': file_path.name
            }
    
    return seed_files

def moveBackwards(seeds_dir: Path, all_files: dict, source_num: int, target_num: int, source_name: str, target_name: str):
    """
    Move a file backwards in the sequence (higher number to lower number)
    Example: Move 044 to 009, increment 009-043 to 010-044
    """
    printIt(f"Moving backwards: {source_num} -> {target_num}", lable.DEBUG)
    
    # Create a temporary directory for safe operations
    temp_dir = seeds_dir / "temp_reorder"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Move source file to temp location
        source_file = all_files[source_num]['path']
        temp_source = temp_dir / f"temp_source_{source_name}.pi"
        shutil.move(str(source_file), str(temp_source))
        printIt(f"Moved {source_file.name} to temporary location", lable.DEBUG)
        
        # Step 2: Shift files from target_num to source_num-1 up by 1
        files_to_shift = []
        for num in range(target_num, source_num):
            if num in all_files:
                files_to_shift.append((num, all_files[num]))
        
        # Sort in reverse order to avoid conflicts
        files_to_shift.sort(reverse=True)
        
        for old_num, file_info in files_to_shift:
            new_num = old_num + 1
            old_path = file_info['path']
            new_name = f"piSeed{new_num:03d}_{file_info['name']}.pi"
            new_path = seeds_dir / new_name
            
            shutil.move(str(old_path), str(new_path))
            printIt(f"Renamed {old_path.name} -> {new_name}", lable.DEBUG)
        
        # Step 3: Move source file to target position
        final_name = f"piSeed{target_num:03d}_{target_name}.pi"
        final_path = seeds_dir / final_name
        shutil.move(str(temp_source), str(final_path))
        printIt(f"Moved source file to {final_name}", lable.INFO)
        
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def moveForwards(seeds_dir: Path, all_files: dict, source_num: int, target_num: int, source_name: str, target_name: str):
    """
    Move a file forwards in the sequence (lower number to higher number)
    Example: Move 009 to 044, decrement 010-044 to 009-043
    """
    printIt(f"Moving forwards: {source_num} -> {target_num}", lable.DEBUG)
    
    # Create a temporary directory for safe operations
    temp_dir = seeds_dir / "temp_reorder"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Move source file to temp location
        source_file = all_files[source_num]['path']
        temp_source = temp_dir / f"temp_source_{source_name}.pi"
        shutil.move(str(source_file), str(temp_source))
        printIt(f"Moved {source_file.name} to temporary location", lable.DEBUG)
        
        # Step 2: Shift files from source_num+1 to target_num down by 1
        files_to_shift = []
        for num in range(source_num + 1, target_num + 1):
            if num in all_files:
                files_to_shift.append((num, all_files[num]))
        
        # Sort in forward order to avoid conflicts
        files_to_shift.sort()
        
        for old_num, file_info in files_to_shift:
            new_num = old_num - 1
            old_path = file_info['path']
            new_name = f"piSeed{new_num:03d}_{file_info['name']}.pi"
            new_path = seeds_dir / new_name
            
            shutil.move(str(old_path), str(new_path))
            printIt(f"Renamed {old_path.name} -> {new_name}", lable.DEBUG)
        
        # Step 3: Move source file to target position
        final_name = f"piSeed{target_num:03d}_{target_name}.pi"
        final_path = seeds_dir / final_name
        shutil.move(str(temp_source), str(final_path))
        printIt(f"Moved source file to {final_name}", lable.INFO)
        
    finally:
        # Clean up temp directory
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

def showPreview(all_files: dict, source_num: int, target_num: int):
    """Show a preview of what changes will be made"""
    printIt("Preview of changes:", lable.INFO)
    
    if source_num > target_num:
        # Moving backwards
        printIt(f"  • {all_files[source_num]['full_name']} -> piSeed{target_num:03d}_{all_files[source_num]['name']}.pi", lable.INFO)
        for num in range(target_num, source_num):
            if num in all_files:
                printIt(f"  • {all_files[num]['full_name']} -> piSeed{num+1:03d}_{all_files[num]['name']}.pi", lable.INFO)
    else:
        # Moving forwards  
        printIt(f"  • {all_files[source_num]['full_name']} -> piSeed{target_num:03d}_{all_files[source_num]['name']}.pi", lable.INFO)
        for num in range(source_num + 1, target_num + 1):
            if num in all_files:
                printIt(f"  • {all_files[num]['full_name']} -> piSeed{num-1:03d}_{all_files[num]['name']}.pi", lable.INFO)
    
    printIt("", lable.INFO)  # Empty line for readability

def validateReorder(seeds_dir: Path):
    """Validate that the reordering was successful"""
    all_files = getAllSeedFiles(seeds_dir)
    numbers = sorted(all_files.keys())
    
    # Check for gaps or duplicates
    expected = list(range(min(numbers), max(numbers) + 1))
    missing = set(expected) - set(numbers)
    
    if missing:
        printIt(f"Warning: Missing piSeed numbers: {sorted(missing)}", lable.WARN)
        return False
    
    printIt(f"Validation successful: piSeed files numbered {min(numbers):03d} to {max(numbers):03d}", lable.INFO)
    return True
