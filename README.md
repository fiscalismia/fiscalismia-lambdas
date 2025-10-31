# fiscalismia-lambdas
AWS Lambda function and layer code written in TypeScript and Python offering process automation for the Fiscalismia Web Service.

### Create Lambda Layers for either Python or TypeScript

**Python**
```bash
cd ~/git/fiscalismia-lambdas/scripts
sudo chmod u+x create_layer_archive.sh
RUNTIME_ENV="python3.13"
DOCKER_IMG="public.ecr.aws/lambda/python:3.13.2025.10.29.20-x86_64"
LAYER_NAME="Fiscalismia_RawDataETL_PythonDependencies"
PROGRAMMING_LANG="python"
PYTHON_V="python3.13"
ENGINE="podman" # podman or docker
bash create_layer_archive.sh ${RUNTIME_ENV} ${DOCKER_IMG} ${LAYER_NAME} ${PROGRAMMING_LANG} ${PYTHON_V} ${ENGINE}

# debug container manually
podman run --rm --entrypoint /bin/bash -it public.ecr.aws/lambda/python:3.13.2025.10.29.20-x86_64
```

**TypeScript**
```bash
cd ~/git/fiscalismia-lambdas/scripts
sudo chmod u+x create_layer_archive.sh
RUNTIME_ENV="nodejs24.x"
DOCKER_IMG="public.ecr.aws/lambda/nodejs:24-preview.2025.10.29.20-x86_64"
LAYER_NAME="Fiscalismia_ImageProcessing_NodeJSDependencies"
PROGRAMMING_LANG="typescript"
NODE_V="node24"
ENGINE="podman" # podman or docker
bash create_layer_archive.sh ${RUNTIME_ENV} ${DOCKER_IMG} ${LAYER_NAME} ${PROGRAMMING_LANG} ${PYTHON_V} ${ENGINE}

# debug container manually
podman run --rm --entrypoint /bin/bash -it public.ecr.aws/lambda/nodejs:24-preview.2025.10.29.20-x86_64
```

### Test the lambda functions locally in Podman
Python: https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions
TypeScript: https://docs.aws.amazon.com/lambda/latest/dg/typescript-image.html