# piSeed Construction Guide

## Table of Contents

1. [Overview](#overview)
2. [piSeed File Structure](#piseed-file-structure)
   - [Basic Syntax](#basic-syntax)
   - [Comments](#comments)
3. [1. piStruct Generation](#1-pistruct-generation)
   - [Required piSeedTypes for piStruct](#required-piseedtypes-for-pistruct)
   - [piScratchDir](#piscratchdir)
   - [piStruct](#pistruct)
   - [piStructS00, piStructC00, piStructD00, piStructL00, piStructA00](#pistructs00-pistructc00-pistructd00-pistructl00-pistructa00)
   - [Important: piStructC00 Cloning Syntax](#important-pistructc00-cloning-syntax)
   - [Example piStruct piSeed](#example-pistruct-piseed)
4. [2. piValuesSetD Generation](#2-pivaluessetd-generation)
   - [Required piSeedTypes for piValuesSetD](#required-piseedtypes-for-pivaluessetd)
   - [piValuesSetD](#pivaluessetd)
   - [piValue](#pivalue)
   - [Example piValuesSetD piSeed](#example-pivaluessetd-piseed)
5. [3. piClassGC Generation](#3-piclassgc-generation)
   - [Required piSeedTypes for piClassGC](#required-piseedtypes-for-piclassgc)
   - [piClassGC](#piclassgc)
   - [piValue (for metadata)](#pivalue-for-metadata)
   - [piValueA (for code arrays)](#pivaluea-for-code-arrays)
   - [piStructA00, piStructC01 (for nested structures)](#pistructa00-pistructc01-for-nested-structures)
   - [Key piClassGC Sections](#key-piclassgc-sections)
   - [Example piClassGC piSeed](#example-piclassgc-piseed)
6. [Structure Cloning: Composition vs Inheritance](#structure-cloning-composition-vs-inheritance)
   - [Composition (Nested Cloning)](#composition-nested-cloning)
   - [Inheritance (Merge Cloning)](#inheritance-merge-cloning)
   - [Key Differences](#key-differences)
   - [Real-World Example](#real-world-example)
7. [piStructA00: Append to Structure](#pistructa00-append-to-structure)
   - [How piStructA00 Works](#how-pistructa00-works)
   - [Example: Building fromImports Structure](#example-building-fromimports-structure)
   - [Key Points About piStructA00](#key-points-about-pistructa00)
   - [Common Pattern](#common-pattern)
8. [piClassGC Code Elements](#piclassgc-code-elements)
   - [Constructor Code Elements](#constructor-code-elements)
   - [Property Generation](#property-generation)
   - [Method Override Elements](#method-override-elements)
   - [Custom Methods and Global Code](#custom-methods-and-global-code)
   - [Code Element Usage Patterns](#code-element-usage-patterns)
9. [4. piDefGC Generation (NEW)](#4-pidefgc-generation-new)
   - [Required piSeedTypes for piDefGC](#required-piseedtypes-for-pidefgc)
   - [Key piDefGC Sections](#key-pidefgc-sections)
   - [Example piDefGC piSeed](#example-pidefgc-piseed)
   - [piDefGC vs piClassGC Differences](#pidefgc-vs-piclassgc-differences)
10. [Processing Order](#processing-order)
11. [File Naming Convention](#file-naming-convention)
12. [Best Practices](#best-practices)
    - [1. Structure Dependencies](#1-structure-dependencies)
    - [2. Default Values](#2-default-values)
    - [3. Code Organization](#3-code-organization)
    - [4. Quoting Rules](#4-quoting-rules)
13. [Common Patterns](#common-patterns)
    - [Simple Data Class](#simple-data-class)
    - [Class with Methods](#class-with-methods)
14. [Troubleshooting](#troubleshooting)
    - [Common Errors](#common-errors)
    - [Validation](#validation)
15. [Summary](#summary)

## Overview

This guide explains how to construct piSeed documents that generate the three types of germ files in the correct order:

1. **piStruct** - Data structure definitions
2. **piValuesSetD** - Default values for structures
3. **piClassGC** - Python class generation configurations

piSeed files are processed sequentially by filename (piSeed000, piSeed001, etc.), so the order matters because later seeds can reference earlier ones.

## piSeed File Structure

### Basic Syntax

Each line in a piSeed file follows this pattern:
```
<piSeedType> <piSeedKey> <piSeedValue>
```

- **piSeedType**: One of 8 types (piScratchDir, piStruct, piValuesSetD, piValue, piClassGC, piValueA, piType, piIndexer)
- **piSeedKey**: The identifier or path for the data
- **piSeedValue**: The value or description (usually in single quotes)

### Comments
```
# This is a comment line
```

## 1. piStruct Generation

piStruct files define the data structure schema for your objects.

### Required piSeedTypes for piStruct:

#### piScratchDir
Sets the output directory for generated files:
```
piScratchDir ./piGerms 'location for storing pis before piIndexing'
```

#### piStruct
Defines the main structure:
```
piStruct <structureName> 'Description of the data structure'
```

#### piSeed Types
Define structure elements with different types:

- **piStructS00** - String field
- **piStructC00** - Clone an existing structure
- **piStructD00** - Dictionary field
- **piStructL00** - List field
- **piStructA00** - Append to structure (creates container for child elements)

```
piStructS00 <fieldName> 'Description of string field'
piStructD01 <fieldName> 'Description of dictionary field (depth 1)'
piStructL02 <fieldName> 'Description of list field (depth 2)'
```

The number suffix (00, 01, 02) indicates the nesting depth.

#### Important: piStructC00 Cloning Syntax

The **piStructC00** clone operation has two distinct syntaxes depending on how you want to incorporate the cloned structure:

**1. Nested Cloning (without period):**
```
piStructC00 <sourceStructure> <targetName>
```
Creates a nested object with the specified name:
```
piStructC00 piProlog piProlog
```
**Result**: Creates `{"piProlog": {cloned piProlog structure}}`

**2. Merge Cloning (with period):**
```
piStructC00 <sourceStructure> <targetName>.
```
The trailing period (`.`) merges all fields from the source structure directly into the current level:
```
piStructC00 pi piClassGC.
```
**Result**: All fields from `pi` structure (piProlog, piBase, piTouch, etc.) become direct children of the current structure, not nested under a `pi` object.

**Why This Matters:**
- **Without period**: Creates composition (has-a relationship)
- **With period**: Creates inheritance (is-a relationship)

The period syntax is crucial for structures like `piClassGC` that need to inherit all standard pi components while adding their own specific fields.

### Example piStruct piSeed:
```
piScratchDir ./piGerms 'location for storing pis'
# piStruct.piProlog
piStruct piProlog 'Defines a data structure for piProlog'
piStructS00 title 'A string value for storing the system name'
piStructS00 version 'A string value for storing the version'
piStructS00 author 'A string value for storing the author'
piStructS00 copyright 'A string value for storing the copyright'
```

**Generates**: `piGerms/piStruct/piStruct_piProlog.json`
```json
{
  "title": "",
  "version": "",
  "author": "",
  "copyright": ""
}
```

## 2. piValuesSetD Generation

piValuesSetD files provide default values for the structures defined in piStruct files.

### Required piSeedTypes for piValuesSetD:

#### piValuesSetD
Declares that default values will be set for a structure:
```
piValuesSetD <structureName> 'defines default values from structure'
```

#### piValue
Sets specific default values:
```
piValue <structureName>.<fieldName> <defaultValue>
```

### Example piValuesSetD piSeed:
```
piValuesSetD piProlog 'defines default prolog values from a piProlog structure'
piValue piProlog.title pi
piValue piProlog.version '0.0.1'
piValue piProlog.author 'martin@pidev.com'
piValue piProlog.copyright '2023 Pi Development'
```

**Generates**: `piGerms/piValuesSetD/piValuesSetD_piProlog.json`
```json
{
  "title": "pi",
  "version": "0.0.1",
  "author": "martin@pidev.com",
  "copyright": "2023 Pi Development"
}
```

## 3. piClassGC Generation

piClassGC files define Python class generation configurations. These are the most complex and depend on both piStruct and piValuesSetD files.

### Required piSeedTypes for piClassGC:

#### piClassGC
Declares a class generation configuration:
```
piClassGC <className> 'Description of the class purpose'
```

#### piValue (for metadata)
Sets class metadata:
```
piValue <className>.piProlog pi.piProlog
piValue <className>.piBase:piType piClassGC
piValue <className>.piBase:piTitle <className>
piValue <className>.piBase:piSD 'Class description'
```

#### piValueA (for code arrays)
Adds code lines to various sections:
```
piValueA <className>.piBody:piClassGC:headers "# Header comment"
piValueA <className>.piBody:piClassGC:imports datetime
piValueA <className>.piBody:piClassGC:strCode "def __str__(self):"
piValueA <className>.piBody:piClassGC:strCode "    return f'Class: {self.name}'"
```

#### piStructA00, piStructC01 (for nested structures)
Define complex nested structures within the class:
```
piStructA00 <className>.piBody:piClassGC:initArguments
piStructC01 argument <argName>.
piValue <className>.piBody:piClassGC:initArguments:<argName>:type str
piValue <className>.piBody:piClassGC:initArguments:<argName>:value "default"
```

### Key piClassGC Sections:

#### Class Definition
```
piValue <className>.piBody:piClassGC:piClassName <PythonClassName>
```

#### Import Statements
```
piValueA <className>.piBody:piClassGC:imports datetime
piValueA <className>.piBody:piClassGC:imports json
```

#### Constructor Arguments
```
piStructA00 <className>.piBody:piClassGC:initArguments
piStructC01 argument <argName>.
piValue <className>.piBody:piClassGC:initArguments:<argName>:type str
piValue <className>.piBody:piClassGC:initArguments:<argName>:value <defaultValue>
```

#### Method Code
```
piValueA <className>.piBody:piClassGC:strCode "def __str__(self):"
piValueA <className>.piBody:piClassGC:strCode "    return 'String representation'"
piValueA <className>.piBody:piClassGC:jsonCode "def json(self) -> dict:"
piValueA <className>.piBody:piClassGC:jsonCode "    return {'key': 'value'}"
```

### Example piClassGC piSeed:
```
# piClass.piBase
piClassGC piBase 'piBase piClass code generator'
piValue piBase.piProlog pi.piProlog
piValue piBase.piBase:piType piClassGC
piValue piBase.piBase:piTitle piBase
piValue piBase.piBase:piSD 'Class to generate piBase objects for pis'
piValueA piBase.piBody:piClassGC:headers "# PiBase generated from piSeed"
piValueA piBase.piBody:piClassGC:imports datetime
piValue piBase.piBody:piClassGC:piClassName PiBase
piStructA00 piBase.piBody:piClassGC:initArguments
piStructC01 argument piType.
piStructC01 argument piTitle.
piStructC01 argument piSD.
piValue piBase.piBody:piClassGC:initArguments:piType:type str
piValue piBase.piBody:piClassGC:initArguments:piType:value pi
piValue piBase.piBody:piClassGC:initArguments:piTitle:type str
piValue piBase.piBody:piClassGC:initArguments:piTitle:value pi
piValue piBase.piBody:piClassGC:initArguments:piSD:type str
piValue piBase.piBody:piClassGC:initArguments:piSD:value 'Base pi object'
```

## Structure Cloning: Composition vs Inheritance

Understanding the difference between nested cloning and merge cloning is crucial for proper piSeed construction.

### Composition (Nested Cloning)
When you want to **include** another structure as a nested component:

```
# piSeed005_piStruct_pi.pi
piStruct pi 'Base pi structure'
piStructC00 piProlog piProlog    # No period - creates nested object
piStructC00 piBase piBase
piStructC00 piTouch piTouch
```

**Generates**:
```json
{
  "pi": {
    "piProlog": {
      "title": "",
      "version": "",
      "author": "",
      "copyright": ""
    },
    "piBase": {
      "piType": "",
      "piTitle": "",
      "piSD": ""
    },
    "piTouch": {
      "piCreationDate": "",
      "piModificationDate": ""
    }
  }
}
```

### Inheritance (Merge Cloning)
When you want to **extend** a structure by inheriting all its fields:

```
# piSeed008_piStruct_piClassGC.pi
piStruct piClassGC 'Data structure for generating code'
piStructC00 pi piClassGC.        # Period - merges all pi fields into piClassGC
piStructA00 piClassGC.piBody     # Add piClassGC-specific fields
```

**Generates**:
```json
{
  "piClassGC": {
    "piProlog": {...},    // Inherited from pi
    "piBase": {...},      // Inherited from pi
    "piTouch": {...},     // Inherited from pi
    "piIndexer": {...},   // Inherited from pi
    "piInfluence": {...}, // Inherited from pi
    "piBody": {           // piClassGC-specific field
      "piClassGC": {...}
    }
  }
}
```

### Key Differences

| Syntax | Purpose | Result | Use Case |
|--------|---------|--------|----------|
| `piStructC00 source target` | Composition | `{"target": {source fields}}` | When you want a nested component |
| `piStructC00 source target.` | Inheritance | `{source fields merged into current level}` | When you want to extend/inherit |

### Real-World Example

**piClassGC needs to be a complete pi object** that can generate Python classes. It inherits all standard pi capabilities and adds class generation features:

```
# Wrong - Creates composition (piClassGC contains a pi object)
piStructC00 pi pi
# Result: {"piClassGC": {"pi": {...}, "piBody": {...}}}

# Correct - Creates inheritance (piClassGC IS a pi object with extensions)
piStructC00 pi piClassGC.
# Result: {"piClassGC": {"piProlog": {...}, "piBase": {...}, "piBody": {...}}}
```

This is why generated piClassGC JSON files have `piProlog`, `piBase`, `piTouch` etc. as direct fields - they inherit the complete pi structure.

## piStructA00: Append to Structure

The **piStructA00** operation is often misunderstood. It doesn't create an array, but rather **appends a new container element** to a structure, which then becomes the target for subsequent child elements.

### How piStructA00 Works

When you use `piStructA00`, it:
1. **Creates a new element** at the specified path
2. **Sets the context** so subsequent piStruct operations add children to this element
3. **Continues until** another piStruct operation changes the context

### Example: Building fromImports Structure

```
# Step 1: Append fromImports container to piClassGC body
piStructA00 piTrie.piBody:piClassGC:fromImports

# Step 2: Clone child elements into the fromImports container
piStructC01 fromImports ast.
piStructC01 fromImports pathlib.
piStructC01 fromImports json.

# Step 3: Add values to the cloned child elements
piValue piTrie.piBody:piClassGC:fromImports:ast:from "ast"
piValue piTrie.piBody:piClassGC:fromImports:ast:import "literal_eval"
piValue piTrie.piBody:piClassGC:fromImports:pathlib:from "pathlib"
piValue piTrie.piBody:piClassGC:fromImports:pathlib:import "Path"
```

**Generates**:
```json
{
  "piTrie": {
    "piBody": {
      "piClassGC": {
        "fromImports": {
          "ast": {
            "from": "ast",
            "import": "literal_eval"
          },
          "pathlib": {
            "from": "pathlib",
            "import": "Path"
          }
        }
      }
    }
  }
}
```

### Key Points About piStructA00

1. **Context Setter**: It establishes where subsequent child elements will be added
2. **Not an Array**: Despite the "A" suffix, it creates a dictionary/object container
3. **Hierarchical Building**: Enables building complex nested structures step by step
4. **Scope**: Subsequent piStructC01, piValue operations target this container until a new piStruct changes context

### Common Pattern

```
# 1. Append container
piStructA00 <path>

# 2. Clone child structures into container
piStructC01 <childStructure> <childName>.

# 3. Set values for child elements
piValue <path>:<childName>:<field> <value>
```

This pattern allows you to build complex nested structures incrementally, which is essential for piClassGC configurations that need detailed import statements, method definitions, and other structured code elements.

## piClassGC Code Elements

piClassGC configurations include several elements that contain user-specified Python code. These elements allow you to customize the generated class behavior beyond the basic structure.

### Constructor Code Elements

#### preSuperInitCode
Lines of code in the `__init__` function that execute **before** the `super(<className>, self).__init__()` call when the class inherits from another class.

```
piValueA MyClass.piBody:piClassGC:preSuperInitCode "self._internal_state = {}"
piValueA MyClass.piBody:piClassGC:preSuperInitCode "self.setup_logging()"
```

**Generated code**:
```python
def __init__(self, ...):
    self._internal_state = {}
    self.setup_logging()
    super(MyClass, self).__init__(...)
    # rest of init code
```

#### postSuperInitCode
Lines of code in the `__init__` function that execute **after** the `super(<className>, self).__init__()` call when the class inherits from another class.

```
piValueA MyClass.piBody:piClassGC:postSuperInitCode "self.configure_instance()"
piValueA MyClass.piBody:piClassGC:postSuperInitCode "self.validate_state()"
```

**Generated code**:
```python
def __init__(self, ...):
    # pre-super code
    super(MyClass, self).__init__(...)
    self.configure_instance()
    self.validate_state()
    # standard init assignments
```

#### initAppendCode
Lines of code in the `__init__` function that go at the **end** when the class does **not** inherit from another class.

```
piValueA MyClass.piBody:piClassGC:initAppendCode "self.finalize_setup()"
piValueA MyClass.piBody:piClassGC:initAppendCode "self.register_callbacks()"
```

**Generated code**:
```python
def __init__(self, ...):
    # standard init assignments
    self.param1 = param1
    self.param2 = param2
    # append code at end
    self.finalize_setup()
    self.register_callbacks()
```

### Property Generation

#### genProps
Flag to add `@property` decorators so initial parameters are treated as class properties with getters/setters.

```
piValue MyClass.piBody:piClassGC:genProps True
```

**Generated code**:
```python
@property
def param1(self):
    return self._param1

@param1.setter
def param1(self, value):
    self._param1 = value
```

### Method Override Elements

#### strCode
Code that **replaces** the default `__str__` class function.

```
piValueA MyClass.piBody:piClassGC:strCode "def __str__(self):"
piValueA MyClass.piBody:piClassGC:strCode "    return f'MyClass(name={self.name}, id={self.id})'"
```

**Generated code**:
```python
def __str__(self):
    return f'MyClass(name={self.name}, id={self.id})'
```

#### jsonCode
Code to **replace** the default code that `genCode.py` creates for the `json()` class function.

```
piValueA MyClass.piBody:piClassGC:jsonCode "def json(self) -> dict:"
piValueA MyClass.piBody:piClassGC:jsonCode "    return {"
piValueA MyClass.piBody:piClassGC:jsonCode "        'name': self.name,"
piValueA MyClass.piBody:piClassGC:jsonCode "        'timestamp': datetime.now().isoformat()"
piValueA MyClass.piBody:piClassGC:jsonCode "    }"
```

**Generated code**:
```python
def json(self) -> dict:
    return {
        'name': self.name,
        'timestamp': datetime.now().isoformat()
    }
```

### Custom Methods and Global Code

#### classDefCode
A **dictionary** of lists of code text that become user-defined functions within the class.

```
piValueA MyClass.piBody:piClassGC:classDefCode "def calculate_total(self, items):"
piValueA MyClass.piBody:piClassGC:classDefCode "    '''Calculate total from list of items'''"
piValueA MyClass.piBody:piClassGC:classDefCode "    return sum(item.value for item in items)"
piValueA MyClass.piBody:piClassGC:classDefCode ""
piValueA MyClass.piBody:piClassGC:classDefCode "def validate_input(self, data):"
piValueA MyClass.piBody:piClassGC:classDefCode "    if not isinstance(data, dict):"
piValueA MyClass.piBody:piClassGC:classDefCode "        raise ValueError('Data must be a dictionary')"
piValueA MyClass.piBody:piClassGC:classDefCode "    return True"
```

**Generated code**:
```python
def calculate_total(self, items):
    '''Calculate total from list of items'''
    return sum(item.value for item in items)

def validate_input(self, data):
    if not isinstance(data, dict):
        raise ValueError('Data must be a dictionary')
    return True
```

#### globalCode
An **array** of code that is appended to the **end** of the class file, allowing global functions to be defined for use by the class.

```
piValueA MyClass.piBody:piClassGC:globalCode "def utility_function(param):"
piValueA MyClass.piBody:piClassGC:globalCode "    '''Global utility function for MyClass'''"
piValueA MyClass.piBody:piClassGC:globalCode "    return param.upper().strip()"
piValueA MyClass.piBody:piClassGC:globalCode ""
piValueA MyClass.piBody:piClassGC:globalCode "GLOBAL_CONSTANT = 'MyClass_Config'"
```

**Generated code** (at end of file):
```python
def utility_function(param):
    '''Global utility function for MyClass'''
    return param.upper().strip()

GLOBAL_CONSTANT = 'MyClass_Config'
```

### Code Element Usage Patterns

#### Multi-line Code Blocks
Each line of code should be a separate `piValueA` entry:
```
piValueA MyClass.piBody:piClassGC:strCode "def __str__(self):"
piValueA MyClass.piBody:piClassGC:strCode "    result = f'MyClass: {self.name}'"
piValueA MyClass.piBody:piClassGC:strCode "    if self.active:"
piValueA MyClass.piBody:piClassGC:strCode "        result += ' (active)'"
piValueA MyClass.piBody:piClassGC:strCode "    return result"
```

#### Empty Lines
Use empty strings for blank lines in code:
```
piValueA MyClass.piBody:piClassGC:classDefCode "def method1(self):"
piValueA MyClass.piBody:piClassGC:classDefCode "    return 'method1'"
piValueA MyClass.piBody:piClassGC:classDefCode ""
piValueA MyClass.piBody:piClassGC:classDefCode "def method2(self):"
piValueA MyClass.piBody:piClassGC:classDefCode "    return 'method2'"
```

#### Code Comments and Docstrings
Include proper Python documentation:
```
piValueA MyClass.piBody:piClassGC:classDefCode "def complex_method(self, data):"
piValueA MyClass.piBody:piClassGC:classDefCode "    ''''"
piValueA MyClass.piBody:piClassGC:classDefCode "    Process complex data with validation."
piValueA MyClass.piBody:piClassGC:classDefCode "    "
piValueA MyClass.piBody:piClassGC:classDefCode "    Args:"
piValueA MyClass.piBody:piClassGC:classDefCode "        data: Input data to process"
piValueA MyClass.piBody:piClassGC:classDefCode "    "
piValueA MyClass.piBody:piClassGC:classDefCode "    Returns:"
piValueA MyClass.piBody:piClassGC:classDefCode "        Processed data result"
piValueA MyClass.piBody:piClassGC:classDefCode "    ''''"
piValueA MyClass.piBody:piClassGC:classDefCode "    # Implementation here"
piValueA MyClass.piBody:piClassGC:classDefCode "    return processed_data"
```

These code elements provide complete control over the generated Python class, allowing you to create sophisticated, fully-functional classes while maintaining the benefits of the piSeed generation system.

piSeed files should be named with a three-digit sequence number:
- `piSeed000_piStruct_<name>.pi` - Structure definitions
- `piSeed001_piStruct_<name>.pi` - More structures
- `piSeed015_piClassGC_<name>.pi` - Class generation configs
- `piSeed044_piDefGC_<name>.pi` - Function definition file generation configs

## 4. piDefGC Generation (NEW)

piDefGC files define Python function definition file generation configurations. These are similar to piClassGC but generate standalone Python files containing only function definitions, stored in the piDefs directory.

### Required piSeedTypes for piDefGC:

#### piDefGC
Declares a function definition file generation configuration:
```
piDefGC <fileName> 'Description of the function file purpose'
```

#### piValue (for metadata)
Sets file metadata:
```
piValue <fileName>.piProlog pi.piProlog
piValue <fileName>.piBase:piType piDefGC
piValue <fileName>.piBase:piTitle <fileName>
piValue <fileName>.piBase:piSD 'File description'
```

#### piValueA (for code arrays)
Adds code lines to various sections:
```
piValueA <fileName>.piBody:piDefGC:headers "# Header comment"
piValueA <fileName>.piBody:piDefGC:imports os
piValueA <fileName>.piBody:piDefGC:functionDefs "def my_function():"
piValueA <fileName>.piBody:piDefGC:functionDefs "    return 'Hello World'"
```

### Key piDefGC Sections:

#### File Definition
```
piValue <fileName>.piBody:piDefGC:fileName <outputFileName>
```

#### Import Statements
```
piValueA <fileName>.piBody:piDefGC:imports os
piValueA <fileName>.piBody:piDefGC:imports sys
```

#### From Imports (same structure as piClassGC)
```
piStructA00 <fileName>.piBody:piDefGC:fromImports
piStructC01 fromImports <moduleName>.
piValue <fileName>.piBody:piDefGC:fromImports:<moduleName>:from "module"
piValue <fileName>.piBody:piDefGC:fromImports:<moduleName>:import "function"
```

#### Function Definitions
```
piStructA00 <fileName>.piBody:piDefGC:functionDefs
piStructL01 <functionName> 'Description of the function'
piValueA <fileName>.piBody:piDefGC:functionDefs:<functionName> "def utility_function(param: str) -> str:"
piValueA <fileName>.piBody:piDefGC:functionDefs:<functionName> "    '''Utility function with documentation'''"
piValueA <fileName>.piBody:piDefGC:functionDefs:<functionName> "    return param.upper()"
piStructL01 <anotherFunction> 'Description of another function'
piValueA <fileName>.piBody:piDefGC:functionDefs:<anotherFunction> "def another_function():"
piValueA <fileName>.piBody:piDefGC:functionDefs:<anotherFunction> "    pass"
```

#### Constants
```
piValueA <fileName>.piBody:piDefGC:constants "DEFAULT_VALUE = 'default'"
piValueA <fileName>.piBody:piDefGC:constants "MAX_SIZE = 1024"
```

#### Global Code
```
piValueA <fileName>.piBody:piDefGC:globalCode "if __name__ == '__main__':"
piValueA <fileName>.piBody:piDefGC:globalCode "    print('Running as main module')"
```

### Example piDefGC piSeed:
```
# Function definitions file
piDefGC utilities 'Utility functions for string and data processing'
piValue utilities.piProlog pi.piProlog
piValue utilities.piBase:piType piDefGC
piValue utilities.piBase:piTitle utilities
piValue utilities.piBase:piSD 'Collection of utility functions'
piValueA utilities.piBody:piDefGC:headers "# Utility Functions"
piValueA utilities.piBody:piDefGC:imports os
piValueA utilities.piBody:piDefGC:imports sys
piStructA00 utilities.piBody:piDefGC:fromImports
piStructC01 fromImports pathlib.
piValue utilities.piBody:piDefGC:fromImports:pathlib:from "pathlib"
piValue utilities.piBody:piDefGC:fromImports:pathlib:import "Path"
piValue utilities.piBody:piDefGC:fileName utilities
piValueA utilities.piBody:piDefGC:constants "DEFAULT_ENCODING = 'utf-8'"
piStructA00 utilities.piBody:piDefGC:functionDefs
piStructL01 clean_string 'Function to clean and normalize strings'
piValueA utilities.piBody:piDefGC:functionDefs:clean_string "def clean_string(text: str) -> str:"
piValueA utilities.piBody:piDefGC:functionDefs:clean_string "    '''Clean and normalize a string'''"
piValueA utilities.piBody:piDefGC:functionDefs:clean_string "    return ' '.join(text.split())"
```

**Generates**: `piDefs/utilities.py`
```python
# Utility Functions
import os
import sys
from pathlib import Path

DEFAULT_ENCODING = 'utf-8'

def clean_string(text: str) -> str:
    '''Clean and normalize a string'''
    return ' '.join(text.split())
```

### piDefGC vs piClassGC Differences:

| Feature | piClassGC | piDefGC |
|---------|-----------|---------|
| Output | Class-based Python files | Function-based Python files |
| Directory | `piClasses/` | `piDefs/` |
| Structure | Class with methods | Standalone functions |
| Constructor | `initArguments` | Not applicable |
| Methods | `classDefCode`, `strCode`, `jsonCode` | `functionDefs` |
| Properties | `genProps` | Not applicable |
| Constants | `globals` (class-level) | `constants` (module-level) |

## Processing Order

1. **piStruct files first** (piSeed000-014) - Define all data structures
2. **piValuesSetD embedded** - Default values are typically in the same files as piStruct
3. **piClassGC files** (piSeed015-043) - Class generation that depends on structures
4. **piDefGC files** (piSeed044+) - Function definition file generation

## File Naming Convention

piSeed files should be named with a three-digit sequence number followed by a descriptive name:

- `piSeed000_piStruct_<name>.pi` - Structure definitions
- `piSeed001_piStruct_<name>.pi` - More structures  
- `piSeed015_piClassGC_<name>.pi` - Class generation configs
- `piSeed044_piDefGC_<name>.pi` - Function definition file generation configs

The sequential numbering ensures proper processing order, as piSeed files are processed in numerical sequence.

## Best Practices

### 1. Structure Dependencies
Always define piStruct before using it in piClassGC:
```
# piSeed008_piStruct_piClassGC.pi - Define the structure
piStruct piClassGC 'Data structure for generating code'
piStructL02 headers 'List of header strings'
piStructS02 piClassName 'Name of the class'

# piSeed015_piClassGC_piPiClasses.pi - Use the structure
piClassGC piPiClasses 'Class that uses piClassGC structure'
piValueA piPiClasses.piBody:piClassGC:headers "# Generated class"
piValue piPiClasses.piBody:piClassGC:piClassName PiPiClasses
```

### 2. Default Values
Provide sensible defaults in piValuesSetD:
```
piValuesSetD piBase 'defines default piBase values'
piValue piBase.piType pi
piValue piBase.piTitle pi
piValue piBase.piSD 'Smallest particle of Pertinent Information'
```

### 3. Code Organization
Group related piValueA statements together:
```
# Headers
piValueA myClass.piBody:piClassGC:headers "# MyClass generated"
piValueA myClass.piBody:piClassGC:headers "# Date: $(date)"

# Imports
piValueA myClass.piBody:piClassGC:imports datetime
piValueA myClass.piBody:piClassGC:imports json

# Methods
piValueA myClass.piBody:piClassGC:strCode "def __str__(self):"
piValueA myClass.piBody:piClassGC:strCode "    return f'{self.__class__.__name__}'"
```

### 4. Quoting Rules
- Use single quotes for descriptions: `'This is a description'`
- Use double quotes for code strings: `"def method(self):"`
- Escape quotes when needed: `"return 'Hello World'"`

## Common Patterns

### Simple Data Class
```
piStruct Person 'A person data structure'
piStructS00 name 'Person name'
piStructS00 email 'Person email'

piValuesSetD Person 'default person values'
piValue Person.name ''
piValue Person.email ''

piClassGC Person 'Person class generator'
piValue Person.piBody:piClassGC:piClassName Person
piStructA00 Person.piBody:piClassGC:initArguments
piStructC01 argument name.
piStructC01 argument email.
piValue Person.piBody:piClassGC:initArguments:name:type str
piValue Person.piBody:piClassGC:initArguments:name:value Person.name
```

### Class with Methods
```
piValueA Calculator.piBody:piClassGC:classDefCode "def add(self, a, b):"
piValueA Calculator.piBody:piClassGC:classDefCode "    return a + b"
piValueA Calculator.piBody:piClassGC:classDefCode ""
piValueA Calculator.piBody:piClassGC:classDefCode "def multiply(self, a, b):"
piValueA Calculator.piBody:piClassGC:classDefCode "    return a * b"
```

## Troubleshooting

### Common Errors

1. **Missing Structure**: Ensure piStruct is defined before using in piClassGC
2. **Quote Mismatch**: Check that quotes are properly matched and escaped
3. **Wrong Order**: piStruct files must be processed before piClassGC files
4. **Path Errors**: Use correct dot notation for nested paths (e.g., `className.piBody:piClassGC:field`)
5. **Cloning Syntax Error**:
   - Use `piStructC00 source target` for nested objects (composition)
   - Use `piStructC00 source target.` for merged fields (inheritance)
   - Missing or extra period changes the entire structure layout
6. **piStructA00 Misunderstanding**:
   - piStructA00 creates a container, not an array
   - Subsequent piStructC01/piValue operations add children to this container
   - Context continues until another piStruct operation changes it

### Validation
Use `piGenCode germSeed <number>` to test individual files:
```bash
piGenCode germSeed 0    # Test piSeed000 file
piGenCode germSeed 15   # Test piSeed015 file
```

## Summary

The piSeed system provides a powerful way to generate structured data and Python classes through a declarative syntax. By following the three-phase approach (piStruct → piValuesSetD → piClassGC), you can create complex, interdependent code generation systems that maintain consistency and reusability.

Remember: **Order matters** - always define structures before using them, and use the sequential numbering system to ensure proper processing order.
