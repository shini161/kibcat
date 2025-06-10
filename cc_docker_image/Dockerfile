# Start from the Cheshire Cat core image
FROM ghcr.io/cheshire-cat-ai/core:latest

# Copy files to the container
COPY update_cat_ui_examples.sh /tmp/update_cat_ui_examples.sh
COPY example_messages.json /tmp/example_messages.json

# Make the script executable and run it during build
RUN apt-get update && \
    apt-get install -y jq && \
    apt-get clean && \
    chmod +x /tmp/update_cat_ui_examples.sh && \
    /tmp/update_cat_ui_examples.sh && \
    rm /tmp/update_cat_ui_examples.sh /tmp/example_messages.json

# Use the default CMD from the parent image