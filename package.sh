#!/bin/bash

# Usage:
# ./package.sh VERSION
# OR
# ./package.sh VERSION --dev

./clean.sh
zip -r ./jpmn-manager.ankiaddon __init__.py version.txt data/ jp-mining-note/ media/ tools/*.py user_files/.placeholder "all_versions/$1-jpmn_example_cards.apkg" config.json

if [[ "$2" == "--dev" ]]; then
    # update zip with manifest
    zip -r ./jpmn-manager.ankiaddon manifest.json
fi
