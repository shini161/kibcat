# Start from the Cheshire Cat core image
FROM ghcr.io/cheshire-cat-ai/core:latest

# Copy files to the container
COPY update_cat_ui.sh /tmp/update_cat_ui.sh
COPY kib-cat-logo.svg /tmp/kib-cat-logo.svg
COPY original_logo_svg.txt /tmp/original_logo_svg.txt
COPY example_messages.json /tmp/example_messages.json
COPY style_override.css /tmp/style_override.css

# Make the script executable and run it during build
RUN apt-get update && \
    apt-get install -y jq nano coreutils && \
    apt-get clean && \
    chmod +x /tmp/update_cat_ui.sh && \
    /tmp/update_cat_ui.sh && \
    rm /tmp/update_cat_ui.sh /tmp/example_messages.json /tmp/style_override.css

# Use the default CMD from the parent image