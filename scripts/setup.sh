#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

# Clone all repos
pushd "$ROOT_DIR"
multi sync
popd

# Set up Python workspace dependencies
cat > ${ROOT_DIR}/web/workspace_requirements.txt << EOF2
-e ../ai-meditation-starter-kit-api
EOF2

# Call the web setup script
pushd ${ROOT_DIR}/web
./scripts/setup
popd


# Call the React install scripts
pushd ${ROOT_DIR}/ai-meditation-starter-kit-react
npm install
popd
pushd ${ROOT_DIR}/react-shared
npm install
popd

# Link the react-shared package
pushd ${ROOT_DIR}/react-shared
npm link
popd
pushd ${ROOT_DIR}/ai-meditation-starter-kit-react
npm link openbase-react-shared
popd


echo "Setup complete! Please restart your IDE, then you can run your project with the VS Code run button."
