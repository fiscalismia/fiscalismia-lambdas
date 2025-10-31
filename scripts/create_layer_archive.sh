#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
# Treat unset variables as an error.
# The return value of a pipeline (chaining)
# is the status of the last command to exit with a non-zero status.
set -euo pipefail

#                      __       ___    __
#    \  /  /\  |    | |  \  /\   |  | /  \ |\ |
#     \/  /~~\ |___ | |__/ /~~\  |  | \__/ | \|
if [ $# -ne 5 ]; then
  echo -e "${RED}ERROR:${NC} Exactly 5 parameters expected."
  echo "Received Parameter count: $#"
  exit 1
fi
if [[ "$4" == "python" ]] || [[ "$4" == "typescript" ]]; then
  echo "PROGRAMMING_LANG: $4"
else
  # -e flag to respect escapes
  echo -e "${RED}ERROR:${NC} Param #4 should be either 'python' or 'typescript'"
  exit 1
fi
zip_binary_dir=$(which zip)
if [[ -z "$zip_binary_dir" ]]; then
  # -e flag to respect escapes
  echo -e "${RED}ERROR:${NC} Please Install the zip package on your local machine"
  exit 1
fi
podman_dir=$(which podman)
if [[ -z "$podman_dir" ]]; then
  # -e flag to respect escapes
  echo -e "${RED}ERROR:${NC} Please Install podman on your local machine"
  exit 1
fi

#               __          __        ___  __
#    \  /  /\  |__) |  /\  |__) |    |__  /__`
#     \/  /~~\ |  \ | /~~\ |__) |___ |___ .__/
RED='\033[0;31m' # ANSI Escape code
NC='\033[0m' # No Color
RUNTIME_ENV=$1
DOCKER_IMG=$2
LAYER_NAME=$3
PROGRAMMING_LANG=$4 # supports python and nodejs
ZIP_NAME="${LAYER_NAME}.zip"
ZIP_DIR="../layers/${LAYER_NAME}"

#            __  ___                              __     __    __      __   ___  __   ___       __   ___       __     ___  __
#    | |\ | /__`  |   /\  |    |        /\  |\ | |  \     / | |__)    |  \ |__  |__) |__  |\ | |  \ |__  |\ | /  ` | |__  /__`
#    | | \| .__/  |  /~~\ |___ |___    /~~\ | \| |__/    /_ | |       |__/ |___ |    |___ | \| |__/ |___ | \| \__, | |___ .__/
podman pull $DOCKER_IMG

##### PYTHON LAYER #####
if [ "${PROGRAMMING_LANG}" == "python" ]; then
  PYTHON_V=$5 # e.g. python3.13
  IMG_VENV_FOLDER="/var/temp/virtualenv"
  LAYER_DIR="../layers/${LAYER_NAME}/python/lib/$PYTHON_V/site-packages"
  # install and persist depdencies locally
  mkdir -p $LAYER_DIR
  podman run --rm --entrypoint /bin/bash -v $LAYER_DIR:/var/task:z $DOCKER_IMG -c "
  mkdir -p $IMG_VENV_FOLDER
  python -m venv $IMG_VENV_FOLDER
  source $IMG_VENV_FOLDER/bin/activate
  cd /var/task

  echo '################## DEPENDENCY INSTALLATION BEGIN ###############'
  pip install requests -t .
  pip install openpyxl -t .
  echo '################## DEPENDENCY INSTALLATION END #################'
  "

  # create zip archive
  cd $ZIP_DIR
  zip -r -q $ZIP_NAME python/
  echo "" && echo ">>>>>>>>>>>>>>>> Zipped installed dependencies to [$ZIP_NAME] <<<<<<<<<<<<<<<<<<<" && echo ""

  # remove locally cached dependencies after zipping
  podman run --rm --entrypoint /bin/bash -v $ZIP_DIR:/var/task:z $DOCKER_IMG -c "
  rm -rf $IMG_VENV_FOLDER
  rm -rf /var/task/python
  "
##### NODEJS LAYER #####
elif [ "${PROGRAMMING_LANG}" == "typescript" ]; then
  # NOT ALWAYS IDENTICAL TO $RUNTIME_ENV
  NODE_V=$5 # e.g. "node24"
  LAYER_DIR="../layers/${LAYER_NAME}/nodejs/$NODE_V/"
  mkdir -p $LAYER_DIR
  podman run --rm --entrypoint /bin/bash -v $LAYER_DIR:/var/task:z $DOCKER_IMG -c "
  ################## DEPENDENCY INSTALLATION BEGIN ###############
  npm i sharp@0.33.5
  ################## DEPENDENCY INSTALLATION END #################
  "

  # create zip archive
  cd $ZIP_DIR
  zip -r -q $ZIP_NAME nodejs
  echo "" && echo ">>>>>>>>>>>>>>>> Zipped installed dependencies to <<<<<<<<<<<<<<<<<<<"
  echo "[$(pwd)/$ZIP_NAME] "

  # remove locally cached dependencies after zipping
  podman run --rm --entrypoint /bin/bash -v $ZIP_DIR:/var/task:z $DOCKER_IMG -c "
  rm -rf nodejs/
  "
fi
