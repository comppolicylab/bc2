#!/bin/bash

CONTAINER_NAME="bc-blob-hks"
ACCOUNT_NAME="blindcharginghks"
DIRECTORY_NAME=$1

if [ -z "$DIRECTORY_NAME" ]; then
  echo "Usage: $0 <directory-name>"
  exit 1
fi

# Define the temporary file for storing pagination results
TEMP_FILE="temp_results.json"
COMBINED_RESULTS="[]"

# Function to combine JSON arrays
combine_json() {
  COMBINED_RESULTS=$(jq -s '[.[][] | objects]' <(echo "$COMBINED_RESULTS") $1)
}

# Retrieve the first page of results
az storage blob list --account-name "$ACCOUNT_NAME" --container-name "$CONTAINER_NAME" --prefix "$DIRECTORY_NAME/" --output json --show-next-marker > $TEMP_FILE
combine_json $TEMP_FILE

# Check for next marker and iterate through pages
NEXT_MARKER=$(jq -r '.[-1].nextMarker' $TEMP_FILE)

while [ "$NEXT_MARKER" != "null" ] && [ "$NEXT_MARKER" != "" ]; do
  az storage blob list --account-name "$ACCOUNT_NAME" --container-name "$CONTAINER_NAME" --prefix "$DIRECTORY_NAME/" --marker "$NEXT_MARKER" --output json --show-next-marker > $TEMP_FILE
  combine_json $TEMP_FILE
  NEXT_MARKER=$(jq -r '.[-1].nextMarker' $TEMP_FILE)
done

# Clean up temporary file
rm $TEMP_FILE

# Count the total number of files
TOTAL_FILES=$(echo "$COMBINED_RESULTS" | jq length)

echo "Total number of files in directory '$DIRECTORY_NAME': $TOTAL_FILES"