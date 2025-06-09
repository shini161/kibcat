#!/bin/bash

# Use the first argument if provided, otherwise use default path
if [ $# -gt 0 ]; then
    file="$1"
else
    file="/admin/assets/cat.js"
fi

# New array value
newArray='["Filtra per i log di errore sul container di devicehub", "Filtra per tutti i log che sono di warning o di informazione", "Filtra per i container di devicehub"]'

# Use sed to replace from 'defaultMessages:[' up to the closing ']'
sed -i "s|defaultMessages:\[[^]]*\]|defaultMessages:$newArray|" "$file"

echo "Replaced defaultMessages array in $file"
