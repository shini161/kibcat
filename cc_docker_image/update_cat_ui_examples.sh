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

# Use sed to replace strings in the JS file
sed -i "s|defaultMessages:\[[^]]*\]|defaultMessages:$newArray|" "$js_file"
sed -i 's/"Cheshire Cat":"You"/"KibCat":"User"/g' "$js_file"
sed -i 's/Cheshire Cat is thinking.../KibCat is thinking.../g' "$js_file"
sed -i 's/Well, well, well, looks like something has gone amiss/Ask the KibCat.../g' "$js_file"
sed -i 's/The enigmatic Cheshire cat is pondering.../Ask the KibCat.../g' "$js_file"
sed -i 's/The curious Cheshire cat is all ears.../Ask the KibCat.../g' "$js_file"
sed -i 's/Ask the Cheshire Cat.../Ask the KibCat.../g' "$js_file"
sed -i 's/🙂/🕵️/g' "$js_file"
sed -i 's/😺/🤖/g' "$js_file"

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
