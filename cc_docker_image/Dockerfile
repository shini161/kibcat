# Start from the Cheshire Cat core image
FROM ghcr.io/cheshire-cat-ai/core:latest

# Copy the update script to the container
COPY update_cat_ui_examples.sh /app/update_cat_ui_examples.sh

# Make the script executable and run it during build
RUN chmod +x /app/update_cat_ui_examples.sh && \
    /app/update_cat_ui_examples.sh

# Use the default CMD from the parent image