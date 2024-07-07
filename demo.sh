#!/bin/bash

# Function to display usage information
usage() {
    echo "Usage: $0 -i INPUT_DIR -o OUTPUT_DIR [-j NUM_JOBS]"
    echo "  -i INPUT_DIR    Specify the input directory containing PDF files."
    echo "  -o OUTPUT_DIR   Specify the output directory for redacted PDF files."
    echo "  -j NUM_JOBS     Specify the number of parallel jobs (default: 10)."
    exit 1
}

# Default number of jobs
NUM_JOBS=10

# Parse command-line arguments
while getopts "i:o:j:" opt; do
    case "$opt" in
        i) INPUT_DIR=$OPTARG ;;
        o) OUTPUT_DIR=$OPTARG ;;
        j) NUM_JOBS=$OPTARG ;;
        *) usage ;;
    esac
done

# Check if input and output directories are provided
if [ -z "$INPUT_DIR" ] || [ -z "$OUTPUT_DIR" ]; then
    usage
fi

export OUTPUT_DIR

find "$INPUT_DIR" -name "*.pdf" | parallel -j "$NUM_JOBS" --eta 'filename=$(basename -- {}); poetry run python -m lib.blind_charging_core ../blind-charging-secrets/demo.toml --input-path {} --output-path "$OUTPUT_DIR/${filename%.pdf}-redacted.pdf"'