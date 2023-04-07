# JPMN Manager

JPMN Manager is a simple Anki add-on that provides a user interface for installing and updating
[jp-mining-note](https://github.com/Aquafina-water-bottle/jp-mining-note/).

> **Note**: If you are familiar with basic command line,
> it is recommended to use the scripts (found under `tools`) directly instead of
> using this add-on.

## Usage
TODO link to documentation

## What this add-on does NOT do
The scope of this add-on is very small, so many features are not supported.

* This add-on does NOT automatically update your note.
* This add-on does NOT notify the user when there are new updates.
* You CANNOT build the note with the add-on, because
    building the note requires various external dependencies that does not come
    with Anki.

## TODO
- get updating working
    - disable text input (no warn?)
    - get permalinks / text output for user changes?
    - is there a dedicated warning QT thing?
    - should message be in a QLabel? is there a standard text box?
- option to run installation script with custom flags
    - https://docs.python.org/3/library/shlex.html#shlex.shlex.whitespace_split
- option to run batch script with custom flags
- upload to ankiweb
