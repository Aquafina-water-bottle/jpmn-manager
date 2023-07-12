#!/bin/bash

# Usage:
# ./package.sh VERSION
# OR
# ./package.sh VERSION --dev

# TODO: add kanji.db to the list of files when supported

./clean.sh
zip -r ./jpmn-manager.ankiaddon __init__.py version.txt data/ jp-mining-note/ media/ tools/*.py user_files/.placeholder "all_versions/$1-jpmn_example_cards.apkg" config.json kanji.py

if [[ "$2" == "--dev" ]]; then
    # update zip with manifest
    zip -r ./jpmn-manager.ankiaddon manifest.json
fi
cp ./jpmn-manager.ankiaddon "./zipped/$1_jpmn-manager.ankiaddon"
