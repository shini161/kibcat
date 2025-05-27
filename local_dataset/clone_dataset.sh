echo NPM version:
npm --version
npm install -g elasticdump

# Variables
REMOTE_ELASTIC_URL="es-logging-devops-pcto.stella.cloud.az.cgm.ag"
LOCAL_ELASTIC_URL="localhost:9200"

# Get passwords
read -p "Enter remote elastic username: " REMOTE_USERNAME
read -s -p "Enter remote elastic password: " REMOTE_PASSWORD
echo
read -p "Enter local elastic username: " LOCAL_USERNAME
read -s -p "Enter local elastic password: " LOCAL_PASSWORD
echo

# Get index names
INDEX_LIST=$(curl -s -u "$REMOTE_USERNAME:$REMOTE_PASSWORD" -k "https://$REMOTE_ELASTIC_URL/_cat/indices?h=index" | awk '{print $1}')
KUBE_INDEXES=$(echo "$INDEX_LIST" | grep '^kube')

# Print result
echo "Available indices:"
echo "$KUBE_INDEXES"

read -p "press enter to download indices"

# Download remote dataset

for index in $KUBE_INDEXES; do
    echo "Downloading index: $index"
    
    NODE_TLS_REJECT_UNAUTHORIZED=0 elasticdump \
    --input=https://"$REMOTE_USERNAME":"$REMOTE_PASSWORD"@"$REMOTE_ELASTIC_URL"/"$index" \
    --output=downloaded_dataset/"$index".json \
    --type=data
    
done

# Upload dataset to local elastic

for index in $KUBE_INDEXES; do
    echo "Uploading index: $index"
    
    NODE_TLS_REJECT_UNAUTHORIZED=0 elasticdump \
    --input=downloaded_dataset/"$index".json \
    --output=http://"$LOCAL_USERNAME":"$LOCAL_PASSWORD"@"$LOCAL_ELASTIC_URL"/"$index" \
    --type=data
    
done

read -p "script completed. press enter to close"