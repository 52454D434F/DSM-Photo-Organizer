#!/usr/bin/env bash
# Script to increment version build number and run package creation

set -e  # Exit on error

VERSION_FILE="source/PhotoOrganizer/VERSION"
PKGCREATE_SCRIPT="./pkgscripts-ng/PkgCreate.py"

# Check if VERSION file exists
if [ ! -f "$VERSION_FILE" ]; then
    echo "Error: VERSION file not found at $VERSION_FILE"
    exit 1
fi

# Read current version
CURRENT_VERSION=$(cat "$VERSION_FILE" | tr -d '\n\r ')

# Validate version format (should be like "1.0.1-00020")
if [[ ! "$CURRENT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+-[0-9]{5}$ ]]; then
    echo "Error: Invalid version format: $CURRENT_VERSION"
    echo "Expected format: MAJOR.MINOR.PATCH-BUILD (e.g., 1.0.1-00020)"
    exit 1
fi

# Extract base version and build number
BASE_VERSION=$(echo "$CURRENT_VERSION" | cut -d'-' -f1)
BUILD_NUMBER=$(echo "$CURRENT_VERSION" | cut -d'-' -f2)

# Increment build number
NEW_BUILD_NUMBER=$((10#$BUILD_NUMBER + 1))

# Format build number with zero-padding (5 digits)
NEW_BUILD_NUMBER_FORMATTED=$(printf "%05d" "$NEW_BUILD_NUMBER")

# Create new version string
NEW_VERSION="${BASE_VERSION}-${NEW_BUILD_NUMBER_FORMATTED}"

# Write new version to file
echo "$NEW_VERSION" > "$VERSION_FILE"

echo "Version incremented: $CURRENT_VERSION -> $NEW_VERSION"

# Check if PkgCreate.py exists
if [ ! -f "$PKGCREATE_SCRIPT" ]; then
    echo "Error: PkgCreate.py not found at $PKGCREATE_SCRIPT"
    exit 1
fi

# Run package creation
echo "Running package creation..."
python3 "$PKGCREATE_SCRIPT" -v 7.2 -c PhotoOrganizer

