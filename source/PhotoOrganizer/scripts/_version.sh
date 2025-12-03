#!/bin/sh
# Shared version loading function for all scripts

# Try multiple locations for VERSION file
# 1. Relative to script location (for build time)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERSION_FILE="$PROJECT_ROOT/VERSION"

# 2. If not found, try installed location (for runtime)
if [ ! -f "$VERSION_FILE" ]; then
    VERSION_FILE="/var/packages/PhotoOrganizer/target/usr/local/PhotoOrganizer/VERSION"
fi

# 3. If still not found, try alternative installed location
if [ ! -f "$VERSION_FILE" ]; then
    VERSION_FILE="/volume1/@appstore/PhotoOrganizer/usr/local/PhotoOrganizer/VERSION"
fi

# Load version
if [ -f "$VERSION_FILE" ]; then
    PACKAGE_VERSION=$(cat "$VERSION_FILE" | tr -d '\n\r ')
else
    # Fallback if VERSION file not found
    PACKAGE_VERSION="1.0.1-00001"
fi

export PACKAGE_VERSION

