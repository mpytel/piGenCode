# piGenCode
## Introduction
**piGenCode** - a Python code generation system that creates classes and function definition files from "piSeed" text files. A piSeeds directory contains these files is a specific order to allow users to construct new computer system architectures. The system uses a structured approach where:

• **piSeed files** contain tuples of information (type, title, short description) call a **pi**
• Each piSeed is a line of text and an instances of a **pi** (<piSeedType> <piSeedKey> <piSeedValue>)
• These get processed or germinated into JSON files stored in the piGerms directory
• Which then generate Python code in piClasses and piDefs directories

There are 8 different piSeedTypes including piStruct (for JSON structure definition), piClassGC (for class definition), piDefGC (for function definition), and others.

**piGenCode** provides commands like germSeed, genCode, syncCode, rmGC, and reorderSeeds for managing the workflow. The system supports distributed file placement, allowing generated files to be placed in any directory structure while maintaining precise tracking and cleanup capabilities.

## Table of Contents

- [piGenCode](#pigencode)
  - [Introduction](#introduction)
  - [Table of Contents](#table-of-contents)
  - [A vision for piGenCode, an instance of pi](#a-vision-for-pigencode-an-instance-of-pi)
  - [Directory Structure](#directory-structure)
  - [Commands](#commands)
    - [germSeed](#germseed)
    - [genCode](#gencode)
    - [rmGC](#rmgc)
    - [syncCode](#synccode)
    - [reorderSeeds](#reorderseeds)
  - [piSeed Types](#piseed-types)
    - [piStruct](#pistruct)
    - [piClassGC](#piclassgc)
    - [piDefGC](#pidefgc)
    - [piValuesSetD](#pivaluessetd)
    - [piValue / piValueA](#pivalue--pivaluea)
  - [Example Workflow](#example-workflow)
  - [Example piSeed Files](#example-piseed-files)
    - [piStruct Example (piSeed001\_piStruct\_piBase.pi)](#pistruct-example-piseed001_pistruct_pibasepi)
    - [piDefGC Example (piSeed045\_piDefGC\_utilities.pi)](#pidefgc-example-piseed045_pidefgc_utilitiespi)
  - [Generated Output](#generated-output)
    - [Python Classes (piClasses/)](#python-classes-piclasses)
    - [Python Functions (piDefs/)](#python-functions-pidefs)
  - [Configuration](#configuration)
  - [Processing Order](#processing-order)

## A vision for piGenCode, an instance of pi
We are developing an idea that uses three string (tokens) called a pi to represent a particle of Pertinent Information, composed of a type, title and short description (SD). This is the dictionary piBase, containing three keys: piType, piTitle, and piSD. When representing a piSeed these elements represent a piSeedType, piSeedKey, and the piSeedValue.

Each piSeedType is an instruction for ***piGenCode*** to perform different operations. Currently there are 8 piSeedTypes:
- piScratchDir
- piStruct
- piValuesSetD
- piValue
- piClassGC
- piDefGC
- piValueA
- piType
- piIndexer

## Directory Structure

```
piGenCode/
├── piSeeds/               # Seed files (numbered piSeed000.pi to piSeedNNN.pi)
├── piGerms/              # Generated JSON configurations (configurable via piScratchDir)
│   ├── piStruct/         # Structure definitions
│   ├── piValuesSetD/     # Default values
│   ├── piClassGC/        # Class generation configs
│   └── piDefGC/          # Function definition configs
├── piClasses/            # Generated Python classes (configurable via piClassGCDir)
└── piDefs/               # Generated Python function files (configurable via piDefGCDir)
```

**Configurable Directories:**
The system supports flexible directory configuration through `.pigencoderc`:
- **piScratchDir**: Location for temporary JSON germ files
- **piClassGCDir**: Base directory for generated Python classes
- **piDefGCDir**: Base directory for generated Python function files
- **Distributed Placement**: Individual files can be placed in custom subdirectories using `fileDirectory` field

## Commands

### germSeed
Process piSeed files to generate JSON configurations and automatically generate Python code.

**Usage:**
```bash
# Process a specific numbered seed file
piGenCode germSeed 45

# Process a specific seed file by name
piGenCode germSeed piSeed045_piDefGC_utilities.pi

# Process all seed files
piGenCode germSeed
```

### genCode
Generate Python code from JSON configurations.

**Usage:**
```bash
# Generate all Python files (classes and functions)
piGenCode genCode

# Generate from specific JSON file
piGenCode genCode piGerms/piClassGC/piClassGC001_piBase.json
piGenCode genCode piGerms/piDefGC/piDefGC001_utilities.json

# Generate using powerful shortcut syntax
piGenCode genCode piClass 21                    # Single piClass file
piGenCode genCode piDef 1-3                     # Range of piDef files
piGenCode genCode piClass 5 7 21                # Multiple specific piClass files
piGenCode genCode piClass 2 8 14-21             # Combination of individual and range
```

### rmGC
Remove generated files to clean up for a fresh start.

**Usage:**
```bash
# Remove generated files while preserving user files
piGenCode rmGC
```

**How it works:**
- **piGerms/**: Removes entire directory (volatile temporary files)
- **piClasses/**: Recursively searches for `.piclass` tracking files and removes only tracked generated files
- **piDefs/**: Recursively searches for `.pidefs` tracking files and removes only tracked generated files
- **User File Safety**: Preserves all user files in configured directories
- **Distributed Support**: Handles files placed in any subdirectory via `fileDirectory` field

**Features:**
- **Selective Removal**: Only removes files that were generated by piGenCode
- **Tracking Files**: Uses `.piclass` and `.pidefs` files to track generated files
- **Recursive Search**: Finds tracking files throughout entire directory trees
- **Status Reporting**: Shows which files were removed vs preserved
- **Error Handling**: Graceful handling of permission issues or missing files
- **Directory Preservation**: Maintains all directory structures and user files

**Example Output:**
```
INFO: Removed directory: piGerms (piGerms)
INFO: Found 3 tracking files in piClasses (src/pigencode/piClasses)
DEBUG: Processing tracking file: src/pigencode/piClasses/models/.piclass
DEBUG: Removed generated file: src/pigencode/piClasses/models/GeneratedModel.py
DEBUG: Preserved 2 user files in src/pigencode/piClasses/models

INFO: Removed directories:
  • piGerms (piGerms)

INFO: Removed generated files:
  • 5 piClass files from 3 locations under src/pigencode/piClasses
  • 3 piDef files from 2 locations under src/pigencode/piDefs

INFO: Preserved user files:
  • 8 user files preserved under src/pigencode/piClasses
  • 4 user files preserved under src/pigencode/piDefs

INFO: Clean-up complete. Generated files removed, user files preserved.
```

### syncCode
Synchronize changes from modified Python files back to their corresponding piSeed files. This command enables reverse-engineering workflow where you can modify generated Python classes and function definition files, then automatically update the piSeed definitions.

**Usage:**
```bash
# Sync all changed files in piClasses and piDefs directories
piGenCode syncCode

# Sync a specific Python file
piGenCode syncCode <filename>
piGenCode syncCode piClasses/piBase.py
piGenCode syncCode piDefs/utilities.py
piGenCode syncCode piBase.py
piGenCode syncCode utilities.py
piGenCode syncCode piBase
piGenCode syncCode utilities
```

**How it works:**
- **AST Analysis**: Parses Python files using Abstract Syntax Tree (AST) to extract code elements
- **Intelligent Mapping**: Maps Python methods and code to corresponding piSeed elements
- **Bidirectional Sync**: Maintains synchronization between generated code and seed definitions
- **Automatic Detection**: Finds corresponding piSeed files automatically for both piClassGC and piDefGC
- **Safe Updates**: Preserves existing piSeed structure while updating modified elements
- **Configurable Directories**: Reads from configured directories specified in .pigencoderc (piClassGCDir and piDefGCDir)

**What gets synchronized:**

**For Python Classes (piClassGC):**
- **Method Bodies**: `__str__`, `json()`, and custom methods
- **Constructor Code**: `__init__` method elements (pre/post super, custom code)
- **Constructor Arguments**: Method parameters with types and default values
- **Import Statements**: Both regular imports and from-imports
- **Global Code**: Module-level functions and code blocks
- **Class Structure**: Method definitions and code organization

**For Python Function Files (piDefGC):**
- **Function Definitions**: Complete function code with docstrings
- **Import Statements**: Both regular imports and from-imports
- **Module Constants**: Module-level variable assignments
- **File Comments**: Module-level docstrings and comments
- **Headers**: File header comments
- **Global Code**: `if __name__ == '__main__':` blocks and other global code

**Code Element Mapping:**

**piClassGC Elements:**
```
Python Method          → piSeed Element
__str__()             → strCode
json()                → jsonCode
__init__() pre-super  → preSuperInitCode
__init__() post-super → postSuperInitCode
__init__() custom     → initAppendCode
__init__() arguments  → initArguments
custom methods        → classDefCode
import statements     → imports / fromImports
global functions      → globalCode
```

**piDefGC Elements:**
```
Python Element         → piSeed Element
function definitions  → functionDefs
import statements     → imports / fromImports
module constants      → constants
file docstring        → fileComment
header comments       → headers
global code blocks    → globalCode
```

**Example Workflows:**

**Class Synchronization:**
```bash
# 1. Generate Python class from piSeed
piGenCode germSeed 19  # Generate piBase class

# 2. Modify the generated Python file
# Edit piClasses/piBase.py - add methods, change __str__, etc.

# 3. Sync changes back to piSeed
piGenCode syncCode piBase.py

# 4. Regenerate to verify
piGenCode genCode piGerms/piClassGC/piClassGC019_piBase.json
```

**Function Definition Synchronization:**
```bash
# 1. Generate Python function file from piSeed
piGenCode germSeed 12  # Generate utilities functions

# 2. Modify the generated Python file
# Edit piDefs/utilities.py - add functions, change constants, etc.

# 3. Sync changes back to piSeed
piGenCode syncCode utilities.py

# 4. Regenerate to verify
piGenCode genCode piGerms/piDefGC/piDefGC012_utilities.json
```

**Features:**
- **Smart Detection**: Automatically finds the correct piSeed file for each Python class or function file
- **Dual Directory Support**: Processes both piClasses/ and piDefs/ directories
- **Incremental Updates**: Only updates changed elements, preserves existing structure
- **Type Inference**: Attempts to infer argument types from Python type hints
- **Import Management**: Handles complex import statements and dependencies
- **Error Handling**: Comprehensive error reporting and validation
- **Batch Processing**: Can process all files in both directories at once

**Example Output:**
```
INFO: Synced 7 changes from utilities.py to piSeed012_piDefGC_utilities.pi
DEBUG:   Updated: headers
DEBUG:   Updated: fileComment
DEBUG:   Updated: imports
DEBUG:   Updated: fromImports
DEBUG:   Updated: constants
DEBUG:   Updated: functionDefs
DEBUG:   Updated: globalCode
INFO: Processed 31 files, made 273 total changes
```

**Use Cases:**
- **Rapid Prototyping**: Modify generated classes and functions directly, then sync back
- **Code Refinement**: Fine-tune generated methods and preserve changes
- **Template Evolution**: Update piSeed templates based on working code
- **Collaborative Development**: Share Python modifications via piSeed updates
- **Version Control**: Keep piSeed files synchronized with code changes
- **Function Development**: Develop utility functions in Python, then sync to piDefGC seeds

### reorderSeeds
Move piSeed files to different positions and automatically renumber all affected files to maintain processing order. This command is essential for organizing the logical flow of seed processing.

**Usage:**
```bash
# Integer shortcut mode (recommended for speed)
piGenCode reorderSeeds <source_number> <target_number>

# File path mode (explicit)
piGenCode reorderSeeds <source_file> <target_file>
```

**Examples:**
```bash
# Move piSeed044 to position 009 (integer shortcut)
piGenCode reorderSeeds 44 9

# Move piSeed015 to position 025 (integer shortcut)
piGenCode reorderSeeds 15 25

# File path mode (same result as first example)
piGenCode reorderSeeds piSeeds/piSeed044_piStruct_piDefGC.pi piSeeds/piSeed009_piStruct_piDefGC.pi
```

**How it works:**
- **Backward Movement** (higher → lower number): Files between target and source positions shift up by 1
- **Forward Movement** (lower → higher number): Files between source and target positions shift down by 1
- **Automatic Renumbering**: All affected files are automatically renumbered to maintain sequence
- **Safe Operations**: Uses temporary directories to prevent data loss
- **Validation**: Confirms sequence integrity after completion

**Features:**
- **Preview Mode**: Shows exactly what changes will be made before executing
- **Integer Shortcuts**: Use simple numbers instead of full file paths
- **Error Handling**: Comprehensive validation and user-friendly error messages
- **Bidirectional**: Supports both forward and backward movements
- **Filename Preservation**: Original filenames are preserved (only numbers change)

**Example Output:**
```
INFO: Moving piSeed044 to position 009
INFO: Preview of changes:
INFO:   • piSeed044_piStruct_piDefGC.pi -> piSeed009_piStruct_piDefGC.pi
INFO:   • piSeed009_piStruct_piUserProfile.pi -> piSeed010_piStruct_piUserProfile.pi
INFO:   • piSeed010_piStruct_piUserBody.pi -> piSeed011_piStruct_piUserBody.pi
INFO:   [... more files ...]
INFO: Successfully reordered piSeed files
```

## piSeed Types

### piStruct
Defines data structures for generating Python classes.

### piClassGC
Generates Python class files with methods, properties, and inheritance. Supports distributed file placement through `fileDirectory` and custom naming through `fileName` fields.

**Key Features:**
- Custom directory placement via `fileDirectory` field
- Custom filename specification via `fileName` field  
- Automatic tracking for selective cleanup
- Full inheritance and method support

### piDefGC
Generates Python function definition files with distributed placement support through `fileDirectory` field:
- Import statements
- Module-level constants
- Function definitions with docstrings
- Global code blocks
- Custom directory placement via `fileDirectory` field
- Custom filename specification via `fileName` field

### piValuesSetD
Defines default values for structures.

### piValue / piValueA
Sets individual values or appends to arrays in structures.

## Example Workflow

1. **Create/Edit piSeed files** in numbered sequence (piSeed000.pi, piSeed001.pi, etc.)
2. **Reorder if needed** using `reorderSeeds` to maintain logical processing order
3. **Clean up (optional)** using `rmGC` to remove existing generated files for a fresh start
4. **Process seeds** using `germSeed` to generate JSON configurations
5. **Generate code** using `genCode` to create Python files
6. **Use generated code** in your projects

## Example piSeed Files

### piStruct Example (piSeed001_piStruct_piBase.pi)
```
piStruct piBase 'Defines a data structure for pi.\nA dictionary for holding pi topic information.'
piStructS00 piType 'piStruct child of pi storing a string type name of the pi.'
piStructS00 piTitle 'piStruct child of pi storing a string title of the pi.'
piStructS00 piSD 'piStruct child of pi storing a short description of the pi.'
```

### piDefGC Example (piSeed045_piDefGC_utilities.pi)
```
piDefGC utilities 'Utility functions for common operations'
piValue utilities.piBody:piDefGC:fileName utilities
piValue utilities.piBody:piDefGC:fileDirectory 'src/utils'
piValueA utilities.piBody:piDefGC:imports os
piValueA utilities.piBody:piDefGC:imports sys
piValueA utilities.piBody:piDefGC:constants "DEFAULT_ENCODING = 'utf-8'"
piStructA00 utilities.piBody:piDefGC:functionDefs
piStructL01 clean_string 'Function to clean and normalize strings'
piValueA utilities.piBody:piDefGC:functionDefs:clean_string "def clean_string(text: str) -> str:"
piValueA utilities.piBody:piDefGC:functionDefs:clean_string "    ''''"
piValueA utilities.piBody:piDefGC:functionDefs:clean_string "    Clean and normalize a string by removing extra whitespace."
piValueA utilities.piBody:piDefGC:functionDefs:clean_string "    ''''"
piValueA utilities.piBody:piDefGC:functionDefs:clean_string "    return ' '.join(text.split())"
```

## Generated Output

### Python Classes (piClasses/)
Generated from piClassGC configurations, these are full-featured Python classes with:
- Constructor methods with type hints
- Properties and methods
- Inheritance support
- JSON serialization
- String representation

### Python Functions (piDefs/)
Generated from piDefGC configurations, these are Python modules with:
- Import statements
- Module-level constants
- Function definitions with docstrings
- Global code blocks

## Configuration

The system uses a `.pigencoderc` file to store configuration settings for directory locations and other options.

**Example .pigencoderc:**
```json
{
  "piSeedsDir": "piSeeds",
  "piScratchDir": "./piGerms",
  "piDefGCDir": "./src/pigencode/piDefs",
  "piClassGCDir": "./src/pigencode/piClasses"
}
```

**Configuration Options:**
- **piSeedsDir**: Directory containing piSeed files
- **piScratchDir**: Location for temporary JSON germ files
- **piDefGCDir**: Base directory for generated Python function files
- **piClassGCDir**: Base directory for generated Python class files

**Distributed File Placement:**
Individual files can override the base directories using the `fileDirectory` field in piSeed configurations, allowing for complex project structures while maintaining organized code generation.

## Processing Order

piSeed files are processed in numerical order (000, 001, 002, etc.), which is why the `reorderSeeds` command is crucial for maintaining the correct logical flow of structure definitions, class generations, and function definitions.