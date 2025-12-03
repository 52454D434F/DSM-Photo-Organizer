#!/bin/bash
# Copyright (c) 2000-2020 Synology Inc. All rights reserved.

source /pkgscripts/include/pkg_util.sh

# Read version from VERSION file
VERSION_FILE="$(dirname "$0")/VERSION"
if [ -f "$VERSION_FILE" ]; then
    version=$(cat "$VERSION_FILE" | tr -d '\n\r ')
else
    version="1.0.1-00001"  # Fallback
fi

package="PhotoOrganizer"
displayname="Photo Organizer and Deduplicator"
os_min_ver="7.0-40000"
maintainer="M -- O --- R .-. C -.-. E ."
distributor="MORCE.code"
arch="noarch"
thirdparty="yes"
silent_install="no"
silent_upgrade="no"
description="Photo Organizer and Deduplicator is an application for automated sorting and deduplication of image (and video) files. Uses EXIF metadata to sort photos by capture date into year-based folders (yyyy/mm_MMM). Continuously monitors a user-defined source directory and organizes new files. Supports duplicate file detection and handling (deleted if equal)."
#dsmuidir="ui"
[ "$(caller)" != "0 NULL" ] && return 0
pkg_dump_info
