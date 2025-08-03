#!/bin/bash

# Check if an argument was provided
if [ -z "$1" ]; then
    echo "Usage: $0 <file_number>"
    exit 1
fi

file_number=$1
i=0

find holdCode/pi -name "*.py" -type f | while read file; do
    original="testCode/pi/${file#holdCode/pi/}"

    # Increment counter and check if it matches the provided number
    i=$((i+1))
    if [ "$i" -eq "$file_number" ] && [ -f "$original" ]; then
        echo "=== Comparing $file with $original ==="
        pigencode fileDiff "$original" "$file"
        break  # Exit the loop once the file is found and processed
    fi
done

# Check if the file number was processed successfully
if [ "$i" -lt "$file_number" ]; then
    echo "Error: File number $file_number not found."
fi