#!/bin/bash

RUNTIME_ENV=$1
DOCKER_IMG=$2
PYTHON_V=$RUNTIME_ENV
ZIP_NAME="$(echo $1)_layer.zip"

DOCKER_VENV_FOLDER="/var/temp/virtualenv"
LAYER_DIR="$(pwd)/raw_data_etl_layer/python/lib/$PYTHON_V/site-packages"
ZIP_DIR="$(pwd)/raw_data_etl_layer"
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

docker pull $DOCKER_IMG

docker run --rm --entrypoint /bin/bash -v $LAYER_DIR:/var/task:z $DOCKER_IMG -c "
mkdir -p $DOCKER_VENV_FOLDER
python -m venv $DOCKER_VENV_FOLDER
source $DOCKER_VENV_FOLDER/bin/activate
cd /var/task

echo '################## DEPENDENCY INSTALLATION BEGIN ###############'
pip install requests -t .
pip install openpyxl -t .
echo '################## DEPENDENCY INSTALLATION END #################'
"

# create zip and then delete node_modules
cd $ZIP_DIR
zip -r -q $ZIP_NAME python/
echo "" && echo ">>>>>>>>>>>>>>>> Zipped installed dependencies to [$ZIP_NAME] <<<<<<<<<<<<<<<<<<<" && echo ""

# clean up local workspace
docker run --rm --entrypoint /bin/bash -v $ZIP_DIR:/var/task:z $DOCKER_IMG -c "
rm -rf $DOCKER_VENV_FOLDER
rm -rf /var/task/python
"
