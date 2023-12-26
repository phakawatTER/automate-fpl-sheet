#!/bin/bash

# Check if the required arguments are provided
if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <requirements_file> <dependency1 dependency2 ...>"
    exit 1
fi

# Extract the first argument as the requirements file
requirements_file="$1"
shift

# The remaining arguments are dependencies to remove
dependencies_to_remove=("$@")

# Create a temporary file to store the modified requirements
temp_file=$(mktemp /tmp/requirements_temp.txt)

# Loop through the original requirements file and exclude specified dependencies
while IFS= read -r line; do
    skip=false
    for dep in "${dependencies_to_remove[@]}"; do
        if [[ "$line" == *"$dep"* ]]; then
            skip=true
            break
        fi
    done
    if [ "$skip" = false ]; then
        echo "$line" >> "$temp_file"
    fi
done < "$requirements_file"

# Replace the original requirements file with the modified one
mv "$temp_file" "$requirements_file"

echo "Modified requirements file: $requirements_file"
