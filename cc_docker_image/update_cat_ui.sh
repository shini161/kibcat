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
sed -i "s|M8.25 4.5a3.75 3.75 0 1 1 7.5 0v8.25a3.75 3.75 0 1 1-7.5 0z|M16.5 4.478v.227a49 49 0 0 1 3.878.512a.75.75 0 1 1-.256 1.478l-.209-.035l-1.005 13.07a3 3 0 0 1-2.991 2.77H8.084a3 3 0 0 1-2.991-2.77L4.087 6.66l-.209.035a.75.75 0 0 1-.256-1.478A49 49 0 0 1 7.5 4.705v-.227c0-1.564 1.213-2.9 2.816-2.951a53 53 0 0 1 3.369 0c1.603.051 2.815 1.387 2.815 2.951m-6.136-1.452a51 51 0 0 1 3.273 0C14.39 3.05 15 3.684 15 4.478v.113a50 50 0 0 0-6 0v-.113c0-.794.609-1.428 1.364-1.452m-.355 5.945a.75.75 0 1 0-1.5.058l.347 9a.75.75 0 1 0 1.499-.058zm5.48.058a.75.75 0 1 0-1.498-.058l-.347 9a.75.75 0 0 0 1.5.058z|" "$js_file"
sed -i "s|M6 10.5a.75.75 0 0 1 .75.75v1.5a5.25 5.25 0 1 0 10.5 0v-1.5a.75.75 0 0 1 1.5 0v1.5a6.75 6.75 0 0 1-6 6.709v2.291h3a.75.75 0 0 1 0 1.5h-7.5a.75.75 0 0 1 0-1.5h3v-2.291a6.75 6.75 0 0 1-6-6.709v-1.5A.75.75 0 0 1 6 10.5|" "$js_file"

echo "Replaced strings in $js_file"

### INJECT CUSTOM CLICK CODE ###
echo "Injecting custom click code in $js_file"

# Create a script tag to execute the click action when the page loads
click_script='
// Custom history clean btn
document.addEventListener("DOMContentLoaded", function() {
    // Wait a bit for the UI to initialize
    setTimeout(function() {
        const baseElement = "#app div.fixed.bottom-0.w-full.items-center.justify-center";
        document.querySelector(`${baseElement} > div button:nth-child(3)`).addEventListener("click", (e) => {
            e.preventDefault();
            const button = document.querySelector(`${baseElement} div.dropdown.dropdown-top > ul > li:nth-child(5) > button`);
            if (button) {
                console.log("Found target button, clicking it");
                button.click();
            } else {
                console.log("Target button not found");
            }
        });
    }, 2000);
});'

# Add at the end of the JS file
if ! grep -q "Custom history clean btn" "$js_file"; then
    echo "Adding Custom history clean btn to $js_file"
    echo -e "\n$click_script" >> "$js_file"
else
    echo "Custom history clean btn already exists in $js_file"
fi

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
