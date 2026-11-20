#!/bin/bash
# Creates a dataset version with DVC and Git
# Run from a bash console as 
#    ./create_dataset_version.sh
# Note, check line endings are LF (not CRLF)
set -euo pipefail

usage() {
    cat <<EOF
Usage: $0 --file <full path to dataset> [--version <version>] [--recover]

Options:
  -f, --file      Full path to the dataset (required)
  -v, --version   Version tag (default: v1; existing tags are never overwritten)
  -r, --recover   Recover this file version (optional)
  -h, --help      Show this help
EOF
    exit 1
}

# Parse options (requires GNU getopt)
PARSED=$(getopt -o f:v:rh -l file:,version:,recover,help -n "$0" -- "$@") || usage
eval set -- "$PARSED"

FILE=""
VERSION="v1"
RECOVER=0

while true; do
    case "$1" in
        -f|--file)    FILE="$2"; shift 2 ;;
        -v|--version) VERSION="$2"; shift 2 ;;
        -r|--recover) RECOVER=1; shift ;;
        -h|--help)    usage ;;
        --)           shift; break ;;
        *)            echo "Internal error parsing options" >&2; exit 1 ;;
    esac
done

# --file is required
[[ -n "$FILE" ]] || { echo "Error: --file is required" >&2; usage; }

if [[ -n $RECOVER == 1 ]] then
    echo "Recover dataset version"
else
    echo "Create dataset version"
fi

echo "Data file: $FILE"
echo "Version: $VERSION"

if [[ -n $RECOVER == 1 ]] then
    # Recover a version from git
    git restore --source="$VERSION" -- "$FILE.dvc"
    # 3. Restore dataset from DVC 
    dvc pull "$FILE.dvc"

else
    # Create
    # Check file exists
    [[ -e "$FILE" ]] || { echo "Error: $FILE not found" >&2; exit 1; }

    # Check version does not already exist
    if git rev-parse -q --verify "refs/tags/$VERSION" >/dev/null; then
        echo "Error: tag $VERSION already exists" >&2
        exit 1
    fi

    # Track the data with DVC (creates/updates $FILE.dvc and a .gitignore entry)
    dvc add "$FILE"
    # Add the *.dvc file to git and version it
    git add "$FILE.dvc"
    # Save the .gitignore
    GITIGNORE="$(dirname "$FILE")/.gitignore"
    [[ -f "$GITIGNORE" ]] && git add "$GITIGNORE"

    git commit -m "Dataset version $VERSION"
    git tag -a "$VERSION" -m "Dataset version $VERSION"

    # Push to remote DVC as backup of the CSV file
    dvc push

    # Push to remote Git repo
    git push --follow-tags
