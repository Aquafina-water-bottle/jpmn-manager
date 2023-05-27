# assumes the jp-mining-note repository is cloned into ../jp-mining-note
# TODO git submodules?

rm -rf tools
rm -rf data
rm -rf jp-mining-note
rm -rf media
rm -rf all_versions

mkdir tools
cp ../jp-mining-note/tools/*.py ./tools
cp -r ../jp-mining-note/data .
cp -r ../jp-mining-note/jp-mining-note .
cp -r ../jp-mining-note/media .
cp -r ../jp-mining-note/all_versions .
cp -r ../jp-mining-note/version.txt .

cp ../kanjivg/kanjivg.db .
