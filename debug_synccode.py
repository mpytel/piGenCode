#!/usr/bin/env python3
"""
Debug script to understand what's causing false changes in syncCode
"""

import sys
import re
import ast
from pathlib import Path

sys.path.insert(0, 'src')
from pigencode.commands.syncCode import extractIfMainCode, extractMethodCode

def debug_global_code_comparison():
    """Debug the global code comparison"""
    
    # Read the Python file
    with open('piDefs/utilities.py', 'r', encoding='utf-8') as f:
        pythonContent = f.read()
    
    # Read the piSeed file
    with open('piSeeds/piSeed010_piDefGC_utilities.pi', 'r', encoding='utf-8') as f:
        seedContent = f.read()
    
    # Parse Python file to extract global code
    tree = ast.parse(pythonContent)
    globalCode = []
    
    for node in tree.body:
        if isinstance(node, ast.If) and hasattr(node.test, 'left') and hasattr(node.test.left, 'id'):
            # Handle if __name__ == '__main__': blocks
            if (node.test.left.id == '__name__' and 
                hasattr(node.test.comparators[0], 's') and 
                node.test.comparators[0].s == '__main__'):
                globalCode.extend(extractIfMainCode(pythonContent, node))
    
    print("=== EXTRACTED GLOBAL CODE FROM PYTHON ===")
    for i, line in enumerate(globalCode):
        print(f"{i:2d}: '{line}'")
    
    # Extract existing global code from piSeed using the NEW regex
    defName = 'utilities'
    globalPattern = rf'^piValueA\s+{re.escape(defName)}\.piBody:piDefGC:globalCode\s+'
    
    existingGlobalCode = []
    lines = seedContent.split('\n')
    for line in lines:
        if re.match(globalPattern, line):
            # Extract the quoted content - use greedy match to handle escaped quotes (NEW REGEX)
            match = re.search(r'"(.*)"$', line)
            if match:
                existingGlobalCode.append(match.group(1))
    
    print("\n=== EXISTING GLOBAL CODE FROM PISEED (NEW REGEX) ===")
    for i, line in enumerate(existingGlobalCode):
        print(f"{i:2d}: '{line}'")
    
    # Normalize both lists by removing trailing empty strings and fix docstring quotes
    def normalize_content(content_list):
        if not content_list:
            return []
        # Make a copy and normalize docstring quotes and escaped quotes
        normalized = []
        for line in content_list:
            # Convert ''' to '''' for consistent comparison
            if line.strip() == "'''":
                normalized_line = "''''"
            else:
                normalized_line = line
            # Unescape quotes for consistent comparison
            normalized_line = normalized_line.replace('\\"', '"')
            normalized.append(normalized_line)
        # Remove trailing empty strings
        while normalized and not normalized[-1].strip():
            normalized.pop()
        return normalized
    
    existing_normalized = normalize_content(existingGlobalCode[:])  # Make copy
    new_normalized = normalize_content(globalCode[:])  # Make copy
    
    print("\n=== NORMALIZED EXISTING GLOBAL CODE ===")
    for i, line in enumerate(existing_normalized):
        print(f"{i:2d}: '{line}'")
    
    print("\n=== NORMALIZED NEW GLOBAL CODE ===")
    for i, line in enumerate(new_normalized):
        print(f"{i:2d}: '{line}'")
    
    print(f"\n=== COMPARISON ===")
    print(f"Are they equal? {existing_normalized == new_normalized}")
    
    if existing_normalized != new_normalized:
        print("Differences found:")
        max_len = max(len(existing_normalized), len(new_normalized))
        for i in range(max_len):
            existing_line = existing_normalized[i] if i < len(existing_normalized) else "<MISSING>"
            new_line = new_normalized[i] if i < len(new_normalized) else "<MISSING>"
            if existing_line != new_line:
                print(f"  Line {i}: '{existing_line}' != '{new_line}'")

if __name__ == "__main__":
    print("=== DEBUGGING SYNCCODE FALSE CHANGES ===")
    debug_global_code_comparison()
