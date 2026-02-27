#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"
TMP_DIR="$( mktemp -d )"

# This script clones the Django allauth example repo and copies files out of it while changing extension.

# Clone the Django allauth example repo
pushd "$TMP_DIR"
git clone https://codeberg.org/allauth/django-allauth.git
popd
echo "Cloned Django allauth example repo to $TMP_DIR"

EXAMPLE_SRC_DIR="$TMP_DIR/django-allauth/examples/react-spa/frontend/src"
TARGET_SRC_DIR="$ROOT_DIR/react-shared/src"

# Copy files from EXAMPLE_SRC_DIR to TARGET_SRC_DIR while changing extension for capitalized files
find "$EXAMPLE_SRC_DIR" -type f -name "*.js" -exec bash -c '
  for f; do
    base=$(basename "$f")
    rel_path="${f#'"$EXAMPLE_SRC_DIR"'/}"
    target_dir="'"$TARGET_SRC_DIR"'/$(dirname "$rel_path")"

    # Create target directory if it doesn'\''t exist
    mkdir -p "$target_dir"

    if [[ $base =~ ^[A-Z] ]]; then
      # Copy and rename to .jsx for capitalized files
      cp "$f" "$target_dir/${base%.js}.jsx"
    else
      # Copy as-is for non-capitalized files
      cp "$f" "$target_dir/$base"
    fi
  done
' bash {} +
