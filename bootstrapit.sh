#!/bin/bash

AUTHOR_NAME="Manuel Barkhau"
AUTHOR_EMAIL="mbarkhau@gmail.com"

KEYWORDS="literate programming markdown"
DESCRIPTION="Literate Programming using Markdown."

LICENSE_ID="MIT"

PACKAGE_NAME="litprog"
MODULE_NAME="litprog"
GIT_REPO_NAMESPACE="mbarkhau"
GIT_REPO_DOMAIN="gitlab.com"

PACKAGE_VERSION="2020.1001-alpha"

DEFAULT_PYTHON_VERSION="python=3.8"
SUPPORTED_PYTHON_VERSIONS="python=3.8 pypy3.6"


IS_PUBLIC=1

## Download and run the actual update script

PROJECT_DIR=$(dirname "$0");

if ! [[ -f "$PROJECT_DIR/scripts/bootstrapit_update.sh" ]]; then
    mkdir -p "$PROJECT_DIR/scripts/";
    RAW_FILES_URL="https://gitlab.com/mbarkhau/bootstrapit/raw/master";
    curl --silent "$RAW_FILES_URL/scripts/bootstrapit_update.sh" \
        > "$PROJECT_DIR/scripts/bootstrapit_update.sh.tmp";
    mv "$PROJECT_DIR/scripts/bootstrapit_update.sh.tmp" \
        "$PROJECT_DIR/scripts/bootstrapit_update.sh";
fi

source "$PROJECT_DIR/scripts/bootstrapit_update.sh";
