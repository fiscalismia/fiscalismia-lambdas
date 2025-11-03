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

### Create Lambda Functions for either Python or TypeScript

```bash
cd ~/git/fiscalismia-lambdas/scripts
sudo chmod u+x create_function_archives.sh
PROGRAMMING_LANG="typescript"
bash create_function_archives.sh ${PROGRAMMING_LANG}

```

### Local TypeScript Lambda Development

```bash
cd ~/git/fiscalismia-lambdas/functions/typescript/Fiscalismia_ImageProcessing
# function dependencies
npm install --save-dev @types/aws-lambda
npm install --save-dev @types/node
npm install --save-dev @types/sharp
# build dependencies
npm install --save-dev esbuild

# build without including aws-sdk/client-s3 in node_modules
# build without including sharp since it is packaged as a layer
npx esbuild index.ts --bundle \
  --minify \
  --platform=node \
  --target=node22 \
  --outfile=dist/index.js \
  --external:@aws-sdk/client-s3 \
  --external:sharp

# or alternatively exclude all packages from node_modules by setting external packages
npx esbuild index.ts --bundle \
  --minify \
  --platform=node \
  --target=node22 \
  --outfile=dist/index.js \
  --packages=external
```

### Test the lambda functions locally in Podman
Python: https://docs.aws.amazon.com/lambda/latest/dg/python-image.html#python-image-instructions
TypeScript: https://docs.aws.amazon.com/lambda/latest/dg/typescript-image.html