#!/bin/bash

js_file="/admin/assets/cat.js"
html_file="/admin/index.html"

absolute_path=$(realpath "$0")
script_dir=$(dirname "$absolute_path")

escape_for_sed() {
    echo "$1" | sed -e 's/[\/&]/\\&/g'
}

### OBTAIN LOGO RESOURCE URL ###
# Read the original logo SVG from file
orig_logo_svg_file="${script_dir}/original_logo_svg.txt"
if [ ! -f "$orig_logo_svg_file" ]; then
    echo "Error: original_logo_svg.txt not found" >&2
    exit 1
fi
orig_logo_svg=$(cat "$orig_logo_svg_file")

# Read file kib-cat-logo.svg and generate data:image/svg+xml,...
logo_url=$(base64 -w 0 "${script_dir}/kib-cat-logo.svg")
logo_url="data:image/svg+xml;base64,${logo_url}"

# Check if the logo URL is not empty
if [ -z "$logo_url" ]; then
    echo "Error: Logo URL is empty" >&2
    exit 1
fi

escaped_orig_logo_svg=$(escape_for_sed "$orig_logo_svg")
escaped_logo_url=$(escape_for_sed "$logo_url")


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
sed -i "s|$escaped_orig_logo_svg|$escaped_logo_url|" "$js_file"

echo "Replaced strings in $js_file"

### UPDATE HTML ###
# Check if source HTML file exists
if [ ! -f "$html_file" ]; then
    echo "Error: index.html not found" >&2
    exit 1
fi

style_override_path="/admin/assets/style_override.css"

# Touch the style_override.css file if it doesn't exist
if [ ! -f "$style_override_path" ]; then
    echo "Creating style_override.css at $style_override_path"
    touch "$style_override_path"
fi

# Add new style in the HTML file after the original style
if ! grep -q "style_override.css" "$html_file"; then
    echo "Adding style_override.css to $html_file"
    sed -i "s|cat.css\">|cat.css\"><link rel=\"stylesheet\" crossorigin href=\"$style_override_path\">|" "$html_file"
else
    echo "style_override.css already exists in $html_file"
fi
