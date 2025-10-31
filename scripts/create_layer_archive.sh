#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
# Treat unset variables as an error.
# The return value of a pipeline (chaining)
# is the status of the last command to exit with a non-zero status.
set -euo pipefail

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
if [ $# -ne 6 ]; then
  echo -e "${RED}ERROR:${NC} Exactly 6 parameters expected."
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

#     __   __   __                      __   __      __   __   __        ___  __
#    |__) /  \ |  \  |\/|  /\  |\ |    /  \ |__)    |  \ /  \ /  ` |__/ |__  |__)
#    |    \__/ |__/  |  | /~~\ | \|    \__/ |  \    |__/ \__/ \__, |  \ |___ |  \
if [[ "$6" == "podman" ]] || [[ "$6" == "docker" ]]; then
  if [[ "$6" == "docker" ]]; then
    function podman()
    {
      docker "$@"
    }
  fi
else
  # -e flag to respect escapes
  echo -e "${RED}ERROR:${NC} Param #6 should be either 'podman' or 'docker'"
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
RUNTIME_ENV=$1
DOCKER_IMG=$2
LAYER_NAME=$3
PROGRAMMING_LANG=$4 # supports python and nodejs
PARENT_DIR="$(dirname $(pwd))"
ZIP_DIR="${PARENT_DIR}/layers/${LAYER_NAME}"
ZIP_NAME="${LAYER_NAME}.zip"
ZIP_FILE="${ZIP_DIR}/${ZIP_NAME}"
#            __  ___                              __     __    __      __   ___  __   ___       __   ___       __     ___  __
#    | |\ | /__`  |   /\  |    |        /\  |\ | |  \     / | |__)    |  \ |__  |__) |__  |\ | |  \ |__  |\ | /  ` | |__  /__`
#    | | \| .__/  |  /~~\ |___ |___    /~~\ | \| |__/    /_ | |       |__/ |___ |    |___ | \| |__/ |___ | \| \__, | |___ .__/
podman pull $DOCKER_IMG

##### PYTHON LAYER #####
if [ "${PROGRAMMING_LANG}" == "python" ]; then
  PYTHON_V=$5 # e.g. python3.13
  IMG_VENV_FOLDER="/var/temp/virtualenv"
  LAYER_DIR="${PARENT_DIR}/layers/${LAYER_NAME}/python/lib/${PYTHON_V}/site-packages"
  # install and persist depdencies locally
  mkdir -p $LAYER_DIR
  podman run --rm --entrypoint /bin/bash -v ${ZIP_DIR}:/var/task:z ${DOCKER_IMG} -c "
  set -euo pipefail
  echo -e \"${BLUE}creating virtual env in ${IMG_VENV_FOLDER}${NC}\"
  mkdir -p ${IMG_VENV_FOLDER}
  python -m venv ${IMG_VENV_FOLDER}
  echo -e \"${BLUE}activating virtual env.${NC}\"
  source ${IMG_VENV_FOLDER}/bin/activate
  echo -e \"${BLUE}python binary used: \$(command -v python)${NC}\"
  cd /var/task
  echo -e \"${BLUE_BOLD}################## DEPENDENCY INSTALLATION BEGIN ###############${NC}\"
  echo [INFO] installing pip packages quietly.
  pip install --quiet -r ./requirements.txt -t ./python/lib/${PYTHON_V}/site-packages/
  echo -e \"${BLUE_BOLD}################## INSTALLED THE FOLLOWING PACKAGES ############${NC}\"
  pip list --path ./python/lib/${PYTHON_V}/site-packages/
  "

  # create zip archive
  cd ${ZIP_DIR}
  rm -f ${ZIP_FILE} || true # remove prior zip if exists
  zip -r -q ${ZIP_NAME} python/
  echo -e "${GREEN_BOLD}==> Zipped installed dependencies to [${ZIP_NAME}]${NC}"

  # remove locally cached dependencies after zipping
  podman run --rm --entrypoint /bin/bash -v ${ZIP_DIR}:/var/task:z ${DOCKER_IMG} -c "
  set -euo pipefail
  echo -e '${YELLOW}Removing python virtual environment: ${IMG_VENV_FOLDER}${NC}'
  rm -rf ${IMG_VENV_FOLDER}
  echo -e '${YELLOW}Removing locally installed python dependencies: /var/task/python${NC}'
  rm -rf /var/task/python
  "
##### NODEJS LAYER #####
elif [ "${PROGRAMMING_LANG}" == "typescript" ]; then
  # NOT ALWAYS IDENTICAL TO $RUNTIME_ENV
  NODE_V=$5 # e.g. "node24"
  podman run --rm --entrypoint /bin/bash -v ${ZIP_DIR}:/var/task:z ${DOCKER_IMG} -c "
  set -euo pipefail
  echo -e \"${BLUE_BOLD}################## DEPENDENCY INSTALLATION BEGIN ###############${NC}\"
  LAYER_DIR=\"nodejs/${NODE_V}\"
  mkdir -p \${LAYER_DIR}
  cp package.json \${LAYER_DIR}
  npm install --prefix \${LAYER_DIR}
  echo -e \"${BLUE_BOLD}################## INSTALLED THE FOLLOWING PACKAGES ############${NC}\"
  ls -hla \${LAYER_DIR}/node_modules/
  "

  # create zip archive
  cd ${ZIP_DIR}
  rm -f ${ZIP_FILE} || true # remove prior zip if exists
  zip -r -q ${ZIP_NAME} nodejs
  echo -e "${GREEN_BOLD}==> Zipped installed dependencies to [${ZIP_NAME}]${NC}"

  # remove locally cached dependencies after zipping
  podman run --rm --entrypoint /bin/bash -v $ZIP_DIR:/var/task:z $DOCKER_IMG -c "
  set -euo pipefail
  echo -e '${YELLOW}Removing locally installed nodejs depdencies: /var/task/nodejs/${NC}'
  rm -rf nodejs/
  "
fi
