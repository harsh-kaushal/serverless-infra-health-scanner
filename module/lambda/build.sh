#!/bin/bash
set -euo pipefail

# Absolute path of this script directory 
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

SOURCE_DIR="${SCRIPT_DIR}/source"
ZIP_NAME="lambda.zip"
ZIP_PATH="${SCRIPT_DIR}/${ZIP_NAME}"

#Clean old files
rm -f "$ZIP_PATH"

# Create a temporary build directory 
BUILD_DIR=$(mktemp -d) trap "rm -rf $BUILD_DIR" EXIT

# Install dependencies into temp build dir (if requirements exists) 
if [[ -f "${SOURCE_DIR}/requirements.txt" ]]; then
  pip install --quiet -r "${SOURCE_DIR}/requirements.txt" -t "$BUILD_DIR"
fi

# Copy python code
cp "${SOURCE_DIR}/lambda_function.py" "$BUILD_DIR"

#Zip it
cd "$BUILD_DIR"
zip -r -q "$ZIP_PATH"

#Compute SHA256 for all files
HASH=$(find "$BUILD_DIR" -type f -print0 | sort -z | xargs -0 sha256sum | sha256sum | awk '{print $1}')

#Output JS0N to Terraform
cat <<<EOF
{ 
  "zip path": "$ZIP_PATH",
  "hash": "$HASH"
}
EOF