#!/bin/bash

RUNTIME_ENV=$1
DOCKER_IMG=$2
NODE_V="node22"
ZIP_NAME="$(echo $1)_layer.zip"

LAYER_DIR="$(pwd)/image_processing_layer/nodejs/$NODE_V/"
ZIP_DIR="$(pwd)/image_processing_layer/"
mkdir -p $LAYER_DIR

RED='\033[0;31m' # ANSI Escape code
NC='\033[0m' # No Color

zip_binary_dir=$(which zip)
if [[ -z "$zip_binary_dir" ]]
  then
    # -e flag to respect escapes
    echo -e "${RED}ERROR:${NC} Please Install the zip package on your local machine"
    exit 1
fi

docker_dir=$(which docker)
if [[ -z "$docker_dir" ]]
  then
    # -e flag to respect escapes
    echo -e "${RED}ERROR:${NC} Please Install docker on your local machine"
    exit 1
fi

docker run --rm --entrypoint /bin/bash -v $LAYER_DIR:/var/task:z $DOCKER_IMG -c "
################## DEPENDENCY INSTALLATION BEGIN ###############
npm i sharp@0.33.5
################## DEPENDENCY INSTALLATION END #################
"

# create zip
cd $ZIP_DIR
zip -r -q $ZIP_NAME nodejs
echo "" && echo ">>>>>>>>>>>>>>>> Zipped installed dependencies to <<<<<<<<<<<<<<<<<<<"
echo "[$(pwd)/$ZIP_NAME] "

docker run --rm --entrypoint /bin/bash -v $ZIP_DIR:/var/task:z $DOCKER_IMG -c "
rm -rf nodejs/
"
# ls -hla