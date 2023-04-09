#!/bin/bash

# Usage:
# ./package.sh VERSION
# OR
# ./package.sh VERSION --dev

rm ./jpmn-manager.ankiaddon
zip -r ./jpmn-manager.ankiaddon __init__.py version.txt data/ jp-mining-note/ media/ tools/ user_files/.placeholder "all_versions/$1-jpmn_example_cards.apkg"

if [[ "$2" == "--dev" ]]; then
    # update zip with manifest
    zip -r ./jpmn-manager.ankiaddon manifest.json
fi
