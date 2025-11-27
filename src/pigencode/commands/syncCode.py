from pathlib import Path
from typing import Tuple #, Dict, List, Optional, Set, Any
from ..classes.argParse import ArgParse
from ..defs.logIt import printIt, label
from ..defs.piSyncCode.piSyncCode import syncSingleFile, syncDirectory, syncAllFiles
from ..defs.piSyncCode.piSyncCodeUtil import printSyncCodeHelp

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

def syncCode(argParse: ArgParse):
    """
    Enhanced synchronize changes from modified Python files back to their corresponding piSeed files.
    This command analyzes changes in piClasses and piDefs directories and updates the appropriate piSeed files.

    Enhanced CLI with options:
    - --dry-run: Show what would be changed without making changes
    - --create-piSeeds: Auto-create piSeed files for specified Python files that don't have piSeeds
    - --validate: Validate sync results and show warnings
    - --stats: Show detailed statistics and change information
    - --filter <type>: Only sync specific file types (class|def|genclass)
    - --exclude-pattern <pattern>: Exclude files matching glob pattern
    """
    # Use the already parsed arguments from ArgParse.__init__
    args = argParse.args
    theArgs = args.arguments
    cmd_options = argParse.cmd_options  # Get the extracted command options

    # Parse enhanced command line options from cmd_options
    options = {
        'dry_run': 'dry-run' in cmd_options,
        'create_piSeeds': 'create-piSeeds' in cmd_options,
        'validate': 'validate' in cmd_options,
        'stats': 'stats' in cmd_options,
        'filter_type': cmd_options.get('filter'),
        'exclude_pattern': cmd_options.get('exclude-pattern'),
        'dest_dir': cmd_options.get('dest-dir'),
        'target_file': None
    }

    # Validate filter type if provided
    if options['filter_type'] and options['filter_type'] not in ['class', 'def', 'genclass']:
        printIt(
            f"Invalid filter type: {options['filter_type']}. Use: class, def, or genclass", label.ERROR)
        return

    # Extract target file from regular arguments (non-option arguments)
    if theArgs:
        options['target_file'] = theArgs[0]

    # Show help if requested
    if 'help' in cmd_options:
        printSyncCodeHelp()
        return

    # Show options if stats requested
    if options['stats']:
        printIt("syncCode Enhanced Options:", label.INFO)
        for key, value in options.items():
            if value is not None and value is not False:
                printIt(f"  {key}: {value}", label.DEBUG)

    # Execute based on options
    if options['target_file']:
        # Sync specific file or directory
        target = options['target_file']
        targetPath = Path(target)

        if targetPath.is_file():
            # Single file
            syncSingleFile(target, options)
        elif targetPath.is_dir():
            # Directory - process all Python files recursively
            syncDirectory(targetPath, options)
        else:
            # Try to find the file/directory
            if not targetPath.exists():
                printIt(f"Target not found: {target}", label.ERROR)
                return
            else:
                printIt(
                    f"Target is neither file nor directory: {target}", label.ERROR)
                return
    else:
        # Sync all files with enhanced options
        syncAllFiles(options)
