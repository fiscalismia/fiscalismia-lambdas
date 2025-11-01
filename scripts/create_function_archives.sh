#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
# Treat unset variables as an error.
# The return value of a pipeline (chaining)
# is the status of the last command to exit with a non-zero status.
set -euo pipefail

PROGRAMMING_LANG=$1 # supports python and typescript

#                      __       ___    __
#    \  /  /\  |    | |  \  /\   |  | /  \ |\ |
#     \/  /~~\ |___ | |__/ /~~\  |  | \__/ | \|
RED='\033[0;31m'        # ANSI 4-bit Escape code
GREEN='\033[0;32m'      # ANSI 4-bit Escape code
YELLOW='\033[0;33m'     # ANSI 4-bit Escape code
BLUE='\033[0;34m'       # ANSI 4-bit Escape code
GREEN_BOLD='\033[1;32m' # ANSI 4-bit Escape code
BLUE_BOLD='\033[1;34m'  # ANSI 4-bit Escape code
NC='\033[0m'            # No Color
CURRENT_DIR=$(pwd | sed 's:.*/::')
if [ "$CURRENT_DIR" != "scripts" ]
then
  echo "please change directory to scripts folder and execute the shell script again."
  exit 1
fi
if [ $# -ne 1 ]; then
  echo -e "${RED}ERROR:${NC} Exactly 1 parameter(s) expected."
  echo "Received Parameter count: $#"
  exit 1
fi
if [[ "$1" == "python" ]] || [[ "$1" == "typescript" ]]; then
  echo "PROGRAMMING_LANG: $1"
else
  # -e flag to respect escapes
  echo -e "${RED}ERROR:${NC} Param #1 should be either 'python' or 'typescript'"
  exit 1
fi
zip_binary_dir=$(which zip)
if [[ -z "$zip_binary_dir" ]]; then
  # -e flag to respect escapes
  echo -e "${RED}ERROR:${NC} Please Install the zip package on your local machine"
  exit 1
fi

PARENT_DIR="$(dirname $(pwd))"
FUNCTION_DIR="${PARENT_DIR}/functions/${PROGRAMMING_LANG}/"
cd ${FUNCTION_DIR}

##### PYTHON FUNCTIONS #####
if [ "${PROGRAMMING_LANG}" == "python" ]; then
  for folder in */; do
    cd ${FUNCTION_DIR}/${folder}
    folder_name=$(echo "${folder}" | sed 's/\/$//')
    zip_name="${folder_name}.zip"
    zip ${zip_name} index.py
    mv ${zip_name} ${FUNCTION_DIR}/
  done
##### TYPERSCRIPT FUNCTIONS #####
elif [ "${PROGRAMMING_LANG}" == "typescript" ]; then
  ls -hla
fi