#!/bin/bash

# Check if a folder path is provided as an argument
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <folder-path>"
    exit 1
fi

FOLDER_PATH=$1
CONTAINER_NAME="bc-blob-hks"
ACCOUNT_NAME="blindcharginghks"

# Function to get blobs with pagination
get_blobs_with_pagination() {
    local marker=""
    local blobs=""
    local page_count=0

    while : ; do
        if [ -z "$marker" ]; then
            response=$(az storage blob list --container-name "$CONTAINER_NAME" --account-name "$ACCOUNT_NAME" --prefix "$FOLDER_PATH" --output json --show-next-marker)
        else
            response=$(az storage blob list --container-name "$CONTAINER_NAME" --account-name "$ACCOUNT_NAME" --prefix "$FOLDER_PATH" --marker "$marker" --output json --show-next-marker)
        fi

        current_blobs=$(echo "$response" | jq -r '.[] | select(.name != null) | .name')
        blobs+=$'\n'"$current_blobs"
        marker=$(echo "$response" | jq -r '.[-1].nextMarker')

        # Debug output to track the markers and counts
        current_count=$(echo "$current_blobs" | wc -l)
        page_count=$((page_count + 1))
        echo "Page $page_count: Retrieved $current_count blobs, marker: $marker"

        if [ -z "$marker" ] || [ "$marker" == "null" ]; then
            break
        fi
    done

    echo "$blobs"
}

# Get the list of all files in the folder from Azure Storage Blob
ALL_FILENAMES=$(get_blobs_with_pagination | tr -s '\n' | grep -v '^$')

# Count the total number of files retrieved
TOTAL_FILES=$(echo "$ALL_FILENAMES" | wc -l)
echo "Total number of files retrieved: $TOTAL_FILES"

# Filter the list to include only PDF files
FILENAMES=$(echo "$ALL_FILENAMES" | grep ".pdf$")

# Count the number of PDF files
NUM_PAGES=$(echo "$FILENAMES" | wc -l)
echo "Number of pages: $NUM_PAGES"

# Count the number of PDF files that end in "001.pdf"
NUM_REPORTS=$(echo "$FILENAMES" | grep "001.pdf$" | wc -l)
echo "Number of reports: $NUM_REPORTS"

# Count the number of distinct file prefixes
NUM_AGENCIES=$(echo "$FILENAMES" | awk -F '__' '{print $1}' | sort | uniq | wc -l)
echo "Number of agencies: $NUM_AGENCIES"