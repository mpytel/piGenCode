#!/bin/bash
find holdCode/pi -name "*.py" -type f | while read file; do
    original="testCode/pi/${file#holdCode/pi/}"
    if [ -f "$original" ]; then
        echo "=== Comparing $file with $original ==="
        pigencode fileDiff $original $file
        #diff_output=$(diff -u "$original" "$file" 2>/dev/null)
    fi
done
