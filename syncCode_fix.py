#!/usr/bin/env python3
"""
Fix for syncCode blank line issue.
This patch modifies the update functions to only report changes when content actually differs.
"""

def updateDefSeedGlobalCode_fixed(seedContent: str, defName: str, globalCode: List[str]) -> Tuple[str, bool]:
    """Update global code in piDefGC seed file - FIXED VERSION"""
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Pattern to match global code
        globalPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:globalCode\s+'
        
        # First, extract existing global code for comparison
        existingGlobalCode = []
        for line in lines:
            if re.match(globalPattern, line):
                # Extract the quoted content
                match = re.search(r'"([^"]*)"$', line)
                if match:
                    existingGlobalCode.append(match.group(1))
                else:
                    # Handle unquoted content (shouldn't happen but be safe)
                    parts = line.split(None, 2)
                    if len(parts) > 2:
                        existingGlobalCode.append(parts[2])
        
        # Compare existing content with new content
        # Normalize both lists by removing trailing empty strings
        existing_normalized = [line for line in existingGlobalCode if line.strip() or any(l.strip() for l in existingGlobalCode[existingGlobalCode.index(line)+1:])]
        new_normalized = [line for line in globalCode if line.strip() or any(l.strip() for l in globalCode[globalCode.index(line)+1:])]
        
        # Only proceed if content is actually different
        if existing_normalized != new_normalized:
            changed = True
        
        i = 0
        foundGlobalCode = False
        
        while i < len(lines):
            line = lines[i]
            
            if re.match(globalPattern, line):
                if not foundGlobalCode:
                    foundGlobalCode = True
                    # Replace with new global code only if changed
                    if changed:
                        for codeLine in globalCode:
                            escapedCode = codeLine.replace('"', '\\"')
                            newLines.append(f'piValueA {defName}.piBody:piDefGC:globalCode "{escapedCode}"')
                    else:
                        # Keep existing content
                        while i < len(lines) and re.match(globalPattern, lines[i]):
                            newLines.append(lines[i])
                            i += 1
                        continue
                
                # Skip all existing global code lines
                while i < len(lines) and re.match(globalPattern, lines[i]):
                    i += 1
                continue
            else:
                newLines.append(line)
                i += 1
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        print(f"Error updating def seed global code: {e}")
        return seedContent, False


def updateDefSeedFunctionDefs_fixed(seedContent: str, defName: str, functionDefs: Dict[str, List[str]]) -> Tuple[str, bool]:
    """Update function definitions in piDefGC seed file - FIXED VERSION"""
    try:
        lines = seedContent.split('\n')
        newLines = []
        changed = False
        
        # Extract existing function definitions for comparison
        existingFunctionDefs = {}
        funcPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:functionDefs:(\w+)\s+'
        
        for line in lines:
            match = re.match(funcPattern, line)
            if match:
                funcName = match.group(1)
                if funcName not in existingFunctionDefs:
                    existingFunctionDefs[funcName] = []
                
                # Extract the quoted content
                contentMatch = re.search(r'"([^"]*)"$', line)
                if contentMatch:
                    existingFunctionDefs[funcName].append(contentMatch.group(1))
        
        # Compare existing with new function definitions
        for funcName, newFuncCode in functionDefs.items():
            existingFuncCode = existingFunctionDefs.get(funcName, [])
            
            # Normalize both by removing trailing empty strings
            existing_normalized = [line for line in existingFuncCode if line.strip() or any(l.strip() for l in existingFuncCode[existingFuncCode.index(line)+1:])]
            new_normalized = [line for line in newFuncCode if line.strip() or any(l.strip() for l in newFuncCode[newFuncCode.index(line)+1:])]
            
            if existing_normalized != new_normalized:
                changed = True
                break
        
        # Only update if there are actual changes
        if not changed:
            return seedContent, False
        
        # Process lines and update function definitions
        i = 0
        processedFunctions = set()
        
        while i < len(lines):
            line = lines[i]
            match = re.match(funcPattern, line)
            
            if match:
                funcName = match.group(1)
                if funcName not in processedFunctions:
                    processedFunctions.add(funcName)
                    
                    # Replace with new function definition
                    if funcName in functionDefs:
                        for funcLine in functionDefs[funcName]:
                            # Fix docstring quotes: convert ''' to ''''
                            if funcLine.strip() == "'''":
                                escapedLine = "''''"
                            else:
                                escapedLine = funcLine.replace('"', '\\"')
                            newLines.append(f'piValueA {defName}.piBody:piDefGC:functionDefs:{funcName} "{escapedLine}"')
                
                # Skip all existing function lines for this function
                while i < len(lines) and re.match(rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:functionDefs:{re.escape(funcName)}\s+', lines[i]):
                    i += 1
                continue
            else:
                newLines.append(line)
                i += 1
        
        return '\n'.join(newLines), changed
        
    except Exception as e:
        print(f"Error updating def seed function definitions: {e}")
        return seedContent, False


def normalize_content_list(content_list):
    """
    Normalize a list of strings by removing trailing empty strings and 
    normalizing whitespace differences that don't matter.
    """
    if not content_list:
        return []
    
    # Remove trailing empty strings
    while content_list and not content_list[-1].strip():
        content_list.pop()
    
    return content_list


if __name__ == "__main__":
    print("This is a patch file for syncCode blank line issues.")
    print("The main issue is that update functions always report changes")
    print("even when content is identical, due to not comparing existing vs new content.")
    print("\nKey fixes:")
    print("1. Extract existing content from piSeed file")
    print("2. Compare with new content from Python file") 
    print("3. Only set changed=True if content actually differs")
    print("4. Normalize content by removing meaningless trailing blank lines")
