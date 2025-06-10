#!/bin/bash

js_file="/admin/assets/cat.js"
css_file="/admin/assets/cat.css"

absolute_path=$(realpath "$0")
script_dir=$(dirname "$absolute_path")

### UPDATE JS ###

# Check if source JS file exists
if [ ! -f "$js_file" ]; then
    echo "Error: cat.js not found" >&2
    exit 1
fi

example_messages_file="${script_dir}/example_messages.json"

# Check if the file exists
if [ ! -f "$example_messages_file" ]; then
    echo "Error: example_messages.json not found" >&2
    exit 1
fi

# Read the file content, parse JSON and convert it to single-line format
newArray=$(jq -c '.' "$example_messages_file")

# Use sed to replace from 'defaultMessages:[' up to the closing ']'
sed -i "s|defaultMessages:\[[^]]*\]|defaultMessages:$newArray|" "$js_file"

echo "Replaced defaultMessages array in $js_file"

### UPDATE CSS ###

# Check if source CSS file exists
if [ ! -f "$css_file" ]; then
    echo "Error: cat.css not found" >&2
    exit 1
fi

style_override_file="${script_dir}/style_override.css"

# Check if the file exists
if [ ! -f "$style_override_file" ]; then
    echo "Error: style_override.css not found" >&2
    exit 1
fi

# Append the content of style_override.css to cat.css
cat "$style_override_file" >> "$css_file"
echo "Appended style_override.css to $css_file"
