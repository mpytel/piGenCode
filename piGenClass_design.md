# piGenClass Design Document

## Overview
Create a new `piGenClass` structure similar to `piDefGC` that can handle multiple classes per file, inheritance, and complex class structures more effectively than the current single-class `piClassGC` approach.

## Key Differences from piClassGC

### piClassGC (Current - Single Class)
- One piSeed file = One class
- Complex inheritance handling
- Limited to single class per file
- Heavy structure with initArguments, etc.

### piGenClass (New - Multiple Classes)
- One piSeed file = One Python file with multiple classes
- Simple class definitions like function definitions
- Handles inheritance naturally
- Lightweight structure similar to piDefGC

## piGenClass Structure

```
piGenClass fileName 'Description of the class file'
piValue fileName.piProlog pi.piProlog
piValue fileName.piBase:piType piGenClass
piValue fileName.piBase:piTitle fileName
piValue fileName.piBase:piSD 'Python class file description'
piValue fileName.piBody:piGenClass:fileDirectory 'path/to/directory'
piValue fileName.piBody:piGenClass:fileName fileName
piValueA fileName.piBody:piGenClass:headers '# Header comments'
piValueA fileName.piBody:piGenClass:imports module_name
piStructA00 fileName.piBody:piGenClass:fromImports
piStructC01 fromImports module_name.
piValue fileName.piBody:piGenClass:fromImports:module_name:from "module"
piValue fileName.piBody:piGenClass:fromImports:module_name:import "items"
piValueA fileName.piBody:piGenClass:constants "CONSTANT = value"
piStructA00 fileName.piBody:piGenClass:classDefs
piStructL01 ClassName 'Description of ClassName'
piValueA fileName.piBody:piGenClass:classDefs:ClassName "class ClassName(BaseClass):"
piValueA fileName.piBody:piGenClass:classDefs:ClassName "    def __init__(self, param):"
piValueA fileName.piBody:piGenClass:classDefs:ClassName "        super().__init__()"
piValueA fileName.piBody:piGenClass:classDefs:ClassName "        self.param = param"
piValueA fileName.piBody:piGenClass:classDefs:ClassName ""
piValueA fileName.piBody:piGenClass:classDefs:ClassName "    def method(self):"
piValueA fileName.piBody:piGenClass:classDefs:ClassName "        return self.param"
piValueA fileName.piBody:piGenClass:globalCode "# Global code at end of file"
```

## Comparison with piDefGC Structure

### piDefGC (Functions)
```
piDefGC fileName 'Function definitions'
piStructA00 fileName.piBody:piDefGC:functionDefs
piStructL01 function_name 'Function description'
piValueA fileName.piBody:piDefGC:functionDefs:function_name "def function_name():"
piValueA fileName.piBody:piDefGC:functionDefs:function_name "    return value"
```

### piGenClass (Classes)
```
piGenClass fileName 'Class definitions'
piStructA00 fileName.piBody:piGenClass:classDefs
piStructL01 ClassName 'Class description'
piValueA fileName.piBody:piGenClass:classDefs:ClassName "class ClassName(BaseClass):"
piValueA fileName.piBody:piGenClass:classDefs:ClassName "    def __init__(self):"
piValueA fileName.piBody:piGenClass:classDefs:ClassName "        super().__init__()"
```

## Benefits of piGenClass

1. **Multiple Classes**: One file can contain multiple class definitions
2. **Natural Inheritance**: Inheritance is just part of the class definition line
3. **Complete Methods**: All methods are captured as part of the class definition
4. **Simpler Structure**: No complex initArguments or method-specific sections
5. **Consistent with piDefGC**: Same pattern as function definitions
6. **Full Fidelity**: Can capture any Python class structure

## Implementation Plan

1. **Create piGenClass piSeed type** - Add to piSeed processing
2. **Modify syncCode** - Detect and create piGenClass files for multi-class files
3. **Create piGenClass generator** - Similar to piDefGC generator
4. **Update file type detection** - Distinguish between piClassGC and piGenClass files
5. **Add to genCode pipeline** - Process piGenClass files

## File Type Detection Logic

```python
def determineClassFileType(pythonFile: Path) -> str:
    """Determine if file should use piClassGC or piGenClass"""
    classes = extractClassesFromFile(pythonFile)
    
    if len(classes) == 1:
        # Single class - could use either, prefer piClassGC for compatibility
        class_info = classes[0]
        if hasComplexStructure(class_info):
            return "piClassGC"  # Complex single class
        else:
            return "piGenClass"  # Simple single class
    elif len(classes) > 1:
        return "piGenClass"  # Multiple classes
    else:
        return "piDefGC"  # No classes, probably functions
```

## Example: piAPIModel.py with piGenClass

```
piGenClass piAPIModel 'Pydantic BaseModel classes for API'
piValue piAPIModel.piProlog pi.piProlog
piValue piAPIModel.piBase:piType piGenClass
piValue piAPIModel.piBase:piTitle piAPIModel
piValue piAPIModel.piBase:piSD 'API model classes with Pydantic BaseModel inheritance'
piValue piAPIModel.piBody:piGenClass:fileDirectory 'src/pigencode/piApi'
piValue piAPIModel.piBody:piGenClass:fileName piAPIModel
piStructA00 piAPIModel.piBody:piGenClass:fromImports
piStructC01 fromImports datetime.
piStructC01 fromImports pydantic.
piStructC01 fromImports typing.
piValue piAPIModel.piBody:piGenClass:fromImports:datetime:from "datetime"
piValue piAPIModel.piBody:piGenClass:fromImports:datetime:import "datetime"
piValue piAPIModel.piBody:piGenClass:fromImports:pydantic:from "pydantic"
piValue piAPIModel.piBody:piGenClass:fromImports:pydantic:import "BaseModel, Field, EmailStr"
piValue piAPIModel.piBody:piGenClass:fromImports:typing:from "typing"
piValue piAPIModel.piBody:piGenClass:fromImports:typing:import "Any, Dict, List"
piStructA00 piAPIModel.piBody:piGenClass:classDefs
piStructL01 PiPrologBM 'Prolog BaseModel class'
piStructL01 PiBaseBM 'Base BaseModel class'
piStructL01 UserSchema 'User schema with validation'
piValueA piAPIModel.piBody:piGenClass:classDefs:PiPrologBM "class PiPrologBM(BaseModel):"
piValueA piAPIModel.piBody:piGenClass:classDefs:PiPrologBM "    title: str"
piValueA piAPIModel.piBody:piGenClass:classDefs:PiPrologBM "    version: str"
piValueA piAPIModel.piBody:piGenClass:classDefs:PiPrologBM "    author: str"
piValueA piAPIModel.piBody:piGenClass:classDefs:PiPrologBM "    copyright: str"
piValueA piAPIModel.piBody:piGenClass:classDefs:PiBaseBM "class PiBaseBM(BaseModel):"
piValueA piAPIModel.piBody:piGenClass:classDefs:PiBaseBM "    piType: str"
piValueA piAPIModel.piBody:piGenClass:classDefs:PiBaseBM "    piTitle: str"
piValueA piAPIModel.piBody:piGenClass:classDefs:PiBaseBM "    piSD: str"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "class UserSchema(BaseModel):"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "    username: str = Field(...)"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "    fullname: str = Field(...)"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "    email: EmailStr = Field(...)"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "    password: str = Field(...)"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "    class Config:"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "        json_schema_extra = {"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "            \"example\": {"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "                \"username\": \"piDev\","
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "                \"fullname\": \"pi dev\","
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "                \"email\": \"pi@pidev.com\","
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "                \"password\": \"pi77dev\""
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "            }"
piValueA piAPIModel.piBody:piGenClass:classDefs:UserSchema "        }"
```

This approach would handle the piAPIModel.py file much more effectively by treating each class as a complete definition rather than trying to fit multiple classes into a single-class structure.
