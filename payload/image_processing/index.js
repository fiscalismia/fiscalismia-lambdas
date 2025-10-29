const fs = require('fs');
const S3 = require("@aws-sdk/client-s3");
const sharp = require("sharp");

const client = new S3.S3Client({
  region: "eu-central-1",
});

//   __   __        __  ___           ___  __
//  /  ` /  \ |\ | /__`  |   /\  |\ |  |  /__`
//  \__, \__/ | \| .__/  |  /~~\ | \|  |  .__/
const processedImageBucket = "hangrybear-fiscalismia-image-storage";
const bucketObject = {
  "Bucket": processedImageBucket,
  "Key": "heidelbeere.jpg"
}

//                   __   __
//  |     /\   |\/| |__) |  \  /\
//  |___ /~~\  |  | |__) |__/ /~~\
exports.handler = async (event) => {

  // ####### Debugging
  // checkDependencies()
  // await listFilesInBucket({bucketName: processedImageBucket})
  // await getSingleObject(bucketObject)
  // await getSingleObjectWithSharp(bucketObject)


  try {
    // Check if the request body exists
    if (!event.body) {
      return {
        statusCode: 400,
        body: JSON.stringify({ message: "No file found in the request body." })
      };
    }

    // Decode the base64-encoded image file from the request body
    const isBase64Encoded = event.isBase64Encoded || false;
    const fileBuffer = isBase64Encoded
      ? Buffer.from(event.body, "base64")
      : Buffer.from(event.body);

    // Log the file size
    console.log(`File size: ${fileBuffer.length} bytes`);

    // Log the file name if provided in headers (e.g., "x-filename" header)
    const fileName = event.headers?.["x-filename"] || "Unknown filename";
    console.log(`File name: ${fileName}`);

    // Return success response
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: "File received successfully.",
        fileName: fileName,
        fileSize: `${fileBuffer.length} bytes`,
      }),
    };
  } catch (error) {
    console.error("Error processing the file:", error);

    return {
      statusCode: 500,
      body: JSON.stringify({ message: "Internal Server Error", error: error.message })
    };
  }
};

//         ___  ___  __                     ___            __  ___    __        __
//  | |\ |  |  |__  |__) |\ |  /\  |       |__  |  | |\ | /  `  |  | /  \ |\ | /__`
//  | | \|  |  |___ |  \ | \| /~~\ |___    |    \__/ | \| \__,  |  | \__/ | \| .__/

// Sharp Integration Testing
const getSingleObjectWithSharp = async (bucketObj) => {
  try {
    const command = new S3.GetObjectCommand(bucketObj);
    const response = await client.send(command);

    const fileStream = response.Body;
    const buffer = await streamToBuffer(fileStream);
    const imageMetadata = await sharp(buffer).metadata();
    const fileSize = response.ContentLength;

    console.log("\nHere's the retrieved image metadata:");
    console.log("Filename:", bucketObj.Key);
    console.log("File size:", fileSize, "bytes");
    console.log("Width:", imageMetadata.width);
    console.log("Height:", imageMetadata.height);
  } catch (err) {
    console.error("Error retrieving or processing the image:", err);
  }
};
// Utility function to convert a stream to a buffer
const streamToBuffer = (stream) => {
  return new Promise((resolve, reject) => {
    const chunks = [];
    stream.on('data', chunk => chunks.push(chunk));
    stream.on('end', () => resolve(Buffer.concat(chunks)));
    stream.on('error', reject);
  });
};

// Lists all contents of an S3 bucket
const listFilesInBucket = async ({ bucketName }) => {
  const command = new S3.ListObjectsV2Command({ Bucket: bucketName });
  const { Contents } = await client.send(command);
  const contentsList = Contents.map((c) => ` • ${c.Key}`).join("\n");
  console.log("\nHere's a list of files in the bucket:");
  console.log(`${contentsList}\n`);
};

// Checks whether or not the depdencies added to the connected layer can be accessed
const checkDependencies = () => {
  try {
    const nodeModulesPath = '/opt/nodejs/node20/node_modules';  // Default path for Lambda layers
    const filesInLayer = fs.readdirSync(nodeModulesPath);
    console.log('Files in /opt/nodejs/node20/node_modules:', filesInLayer);

    return {
      statusCode: 200,
      body: JSON.stringify({ success: 'Layer can be accessed' }),
    };
  } catch (error) {
    console.error('Error:', error);
    return {
      statusCode: 500,
      body: JSON.stringify({ error: 'Failed to access the dependencies from the layer' }),
    };
  }
}