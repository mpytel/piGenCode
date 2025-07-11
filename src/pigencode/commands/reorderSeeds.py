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
        piGenCode reorderSeeds                                    # Auto-compact gaps
    
    Examples:
        piGenCode reorderSeeds piSeeds/piSeed044_piStruct_piDefGC.pi piSeeds/piSeed009_piStruct_piDefGC.pi
        piGenCode reorderSeeds 44 9
        piGenCode reorderSeeds                                    # Remove gaps in numbering
    
    Auto-compact mode (no arguments):
    - Detects gaps in piSeed file numbering
    - Renumbers files to collapse gaps (e.g., 000,001,003,005 -> 000,001,002,003)
    - Preserves original order
    - Skips compacting if highest number is >10 numbers away (indicates intentional offset)
    """
    args = argParse.parser.parse_args()
    theArgs = args.arguments
    
    # Get piSeeds directory first
    seeds_dir = getSeedPath()
    if not seeds_dir:
        printIt("Could not find piSeeds directory", lable.ERROR)
        return
    
    # Get all piSeed files for reference
    all_seed_files = getAllSeedFiles(seeds_dir)
    
    # Auto-compact mode when no arguments provided
    if len(theArgs) == 0:
        return autoCompactSeeds(seeds_dir, all_seed_files)
    
    if len(theArgs) != 2:
        printIt("Usage: piGenCode reorderSeeds <source_file> <target_file>", lable.ERROR)
        printIt("   OR: piGenCode reorderSeeds <source_number> <target_number>", lable.ERROR)
        printIt("   OR: piGenCode reorderSeeds                                    # Auto-compact gaps", lable.ERROR)
        printIt("Examples:", lable.INFO)
        printIt("  piGenCode reorderSeeds piSeeds/piSeed044_piStruct_piDefGC.pi piSeeds/piSeed009_piStruct_piDefGC.pi", lable.INFO)
        printIt("  piGenCode reorderSeeds 44 9", lable.INFO)
        printIt("  piGenCode reorderSeeds                                    # Remove gaps in numbering", lable.INFO)
        return
    
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

def autoCompactSeeds(seeds_dir: Path, all_seed_files: dict) -> None:
    """
    Auto-compact piSeed files by removing gaps in numbering.
    
    Args:
        seeds_dir: Path to piSeeds directory
        all_seed_files: Dictionary of existing seed files {number: file_info}
    
    Logic:
        - Find gaps in numbering sequence
        - Renumber files to collapse gaps while preserving order
        - Skip if highest number is >10 away from expected (indicates intentional offset)
    """
    if not all_seed_files:
        printIt("No piSeed files found to compact", lable.INFO)
        return
    
    # Get sorted list of existing numbers
    existing_numbers = sorted(all_seed_files.keys())
    min_num = existing_numbers[0]
    max_num = existing_numbers[-1]
    expected_max = min_num + len(existing_numbers) - 1
    
    printIt(f"Found {len(existing_numbers)} piSeed files: {min_num:03d} to {max_num:03d}", lable.INFO)
    
    # Check if there are gaps
    expected_sequence = list(range(min_num, min_num + len(existing_numbers)))
    if existing_numbers == expected_sequence:
        printIt("No gaps found - piSeed files are already properly numbered", lable.INFO)
        return
    
    # Check for intentional offset (>10 gap from expected)
    if max_num - expected_max > 10:
        printIt(f"Large gap detected ({max_num - expected_max} numbers). This appears to be intentional offset.", lable.INFO)
        printIt("Skipping auto-compact. Use explicit reorderSeeds if you want to compact anyway.", lable.INFO)
        return
    
    # Show what gaps will be removed
    gaps = []
    for i in range(min_num, max_num + 1):
        if i not in existing_numbers:
            gaps.append(i)
    
    if gaps:
        printIt(f"Gaps found: {[f'{g:03d}' for g in gaps]}", lable.INFO)
        printIt("Compacting piSeed files to remove gaps...", lable.INFO)
    
    # Create renaming plan
    renaming_plan = []
    new_number = min_num
    
    for old_number in existing_numbers:
        if old_number != new_number:
            file_info = all_seed_files[old_number]
            old_path = file_info['path']
            new_filename = f"piSeed{new_number:03d}_{file_info['name']}.pi"
            new_path = seeds_dir / new_filename
            
            renaming_plan.append({
                'old_number': old_number,
                'new_number': new_number,
                'old_path': old_path,
                'new_path': new_path,
                'name': file_info['name']
            })
        
        new_number += 1
    
    if not renaming_plan:
        printIt("No renaming needed", lable.INFO)
        return
    
    # Show preview of changes
    printIt("Preview of changes:", lable.INFO)
    for item in renaming_plan:
        printIt(f"  • piSeed{item['old_number']:03d}_{item['name']}.pi -> piSeed{item['new_number']:03d}_{item['name']}.pi", lable.INFO)
    
    # Confirm with user (in a real implementation, you might want user confirmation)
    # For now, proceed automatically
    
    # Create temporary directory for safe renaming
    temp_dir = seeds_dir / ".temp_reorder"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Step 1: Move all files to temporary directory
        temp_files = []
        for item in renaming_plan:
            temp_file = temp_dir / item['old_path'].name
            shutil.move(str(item['old_path']), str(temp_file))
            temp_files.append((temp_file, item['new_path']))
            printIt(f"Moved {item['old_path'].name} to temporary location", lable.DEBUG)
        
        # Step 2: Move files back with new names
        for temp_file, new_path in temp_files:
            shutil.move(str(temp_file), str(new_path))
            printIt(f"Renamed to {new_path.name}", lable.DEBUG)
        
        # Clean up temporary directory
        temp_dir.rmdir()
        
        printIt(f"Successfully compacted {len(renaming_plan)} piSeed files", lable.INFO)
        printIt(f"piSeed files now numbered: {min_num:03d} to {min_num + len(existing_numbers) - 1:03d}", lable.INFO)
        
    except Exception as e:
        printIt(f"Error during compacting: {e}", lable.ERROR)
        # Try to restore files from temp directory
        try:
            for temp_file in temp_dir.glob("*.pi"):
                original_path = seeds_dir / temp_file.name
                if not original_path.exists():
                    shutil.move(str(temp_file), str(original_path))
            temp_dir.rmdir()
            printIt("Restored files from temporary directory", lable.INFO)
        except:
            printIt(f"Manual cleanup may be needed in {temp_dir}", lable.WARN)
