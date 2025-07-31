#!/bin/bash
find holdCode/cmdpackage -name "*.py" -type f | while read file; do
    original="testCode/cmdpackage/${file#holdCode/cmdpackage/}"
    if [ -f "$original" ]; then
        echo "=== Comparing $file with $original ==="
        pigencode fileDiff $original $file
        #diff_output=$(diff -u "$original" "$file" 2>/dev/null)
    fi
done
