#!/bin/bash
# Copyright (c) 2000-2020 Synology Inc. All rights reserved.

source /pkgscripts/include/pkg_util.sh

# Read version from VERSION file
VERSION_FILE="$(dirname "$0")/VERSION"
if [ -f "$VERSION_FILE" ]; then
    version=$(cat "$VERSION_FILE" | tr -d '\n\r ')
else
    version="1.0.0-00001"  # Fallback
fi

package="Json-Server"
displayname="JSON Server"
os_min_ver="7.0-40000"
maintainer="M -- O --- R .-. C -.-. E ."
maintainer_url="https://github.com/52454D434F/"
distributor="MORCE.codes"
distributor_url="https://morce.codes"
arch="noarch"
thirdparty="yes"
silent_install="no"
silent_upgrade="no"
description="JSON Server is a Node.js package that provides a REST API server from a JSON file. This package installs and runs json-server on your Synology NAS, allowing you to quickly create a mock REST API for development and testing purposes."
#dsmuidir="ui"
[ "$(caller)" != "0 NULL" ] && return 0
pkg_dump_info
