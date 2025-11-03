import * as fs from 'fs';
import {
  S3Client,
  GetObjectCommand,
  ListObjectsV2Command,
  GetObjectCommandInput,
  GetObjectCommandOutput,
  _Object // Type for S3 object content listing
} from "@aws-sdk/client-s3";
import sharp, { Metadata } from "sharp"; // Import sharp default and Metadata type
import { Readable } from 'stream'; // For typing Node.js streams
import { APIGatewayProxyEvent, APIGatewayProxyResult } from 'aws-lambda';

const client: S3Client = new S3Client({
  region: "eu-central-1",
});

//   __   __        __  ___           ___  __
//  /  ` /  \ |\ | /__`  |   /\  |\ |  |  /__`
//  \__, \__/ | \| .__/  |  /~~\ | \|  |  .__/
const processedImageBucket: string = "fiscalismia-image-storage";

// Use the imported S3 type for the input
const bucketObject: GetObjectCommandInput = {
  "Bucket": processedImageBucket,
  "Key": "1356548.png"
}

//                   __   __
//  |     /\   |\/| |__) |  \  /\
//  |___ /~~\  |  | |__) |__/ /~~\
export const lambda_handler = async (event: APIGatewayProxyEvent): Promise<APIGatewayProxyResult> => {

  // ####### Debugging
  checkDependencies(); // This function's return value isn't used, preserving original logic.
  await listFilesInBucket({ bucketName: processedImageBucket });
  // Note: Removed call to the undefined 'getSingleObject' function from your original file.
  await getSingleObjectWithSharp(bucketObject);

  try {
    // Check if the request body exists
    if (!event.body) {
      return {
        statusCode: 400,
        body: JSON.stringify({ message: "No file found in the request body." })
      };
    }

    // Decode the base64-encoded image file from the request body
    const isBase64Encoded: boolean = event.isBase64Encoded || false;
    const fileBuffer: Buffer = isBase64Encoded
      ? Buffer.from(event.body, "base64")
      : Buffer.from(event.body);

    // Log the file size
    console.log(`File size: ${fileBuffer.length} bytes`);

    // Log the file name (using optional chaining for safety)
    const fileName: string = event.headers?.["x-filename"] || "Unknown filename";
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
  } catch (error: unknown) { // Type catch block error as 'unknown'
    console.error("Error processing the file:", error);

    return {
      statusCode: 500,
      body: JSON.stringify({
        message: "Internal Server Error",
        // Assert error as Error type to access .message
        error: (error as Error).message
      })
    };
  }
};

//         ___  ___  __                     ___            __  ___    __        __
//  | |\ |  |  |__  |__) |\ |  /\  |       |__  |  | |\ | /  `  |  | /  \ |\ | /__`
//  | | \|  |  |___ |  \ | \| /~~\ |___    |    \__/ | \| \__,  |  | \__/ | \| .__/

// Sharp Integration Testing
// Type the function argument and return type (Promise<void> as it only logs)
const getSingleObjectWithSharp = async (bucketObj: GetObjectCommandInput): Promise<void> => {
  try {
    const command = new GetObjectCommand(bucketObj);
    const response: GetObjectCommandOutput = await client.send(command);

    // Best practice: Check if the body exists before processing
    if (!response.Body) {
      throw new Error("S3 object response body is empty.");
    }

    // Cast the body to Node's Readable stream type
    const fileStream = response.Body as Readable;
    const buffer: Buffer = await streamToBuffer(fileStream);
    const imageMetadata: Metadata = await sharp(buffer).metadata();
    const fileSize: number | undefined = response.ContentLength;

    console.log("\nHere's the retrieved image metadata:");
    console.log("Filename:", bucketObj.Key);
    console.log("File size:", fileSize || "Unknown", "bytes"); // Handle potentially undefined size
    console.log("Width:", imageMetadata.width);
    console.log("Height:", imageMetadata.height);
  } catch (err: unknown) {
    console.error("Error retrieving or processing the image:", (err as Error).message);
  }
};

// Utility function to convert a stream to a buffer
// Type the stream argument and the Promise return value
const streamToBuffer = (stream: Readable): Promise<Buffer> => {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = []; // Type the array
    stream.on('data', (chunk: Buffer) => chunks.push(chunk)); // Type the chunk
    stream.on('end', () => resolve(Buffer.concat(chunks)));
    stream.on('error', reject);
  });
};

// Lists all contents of an S3 bucket
// Type the argument object and return type
const listFilesInBucket = async ({ bucketName }: { bucketName: string }): Promise<void> => {
  try {
    const command = new ListObjectsV2Command({ Bucket: bucketName });
    const { Contents } = await client.send(command);

    // Handle empty or non-existent bucket contents
    if (!Contents || Contents.length === 0) {
      console.log("\nBucket is empty or no contents found.\n");
      return;
    }

    const contentsList: string = Contents
      .map((c: _Object) => ` • ${c.Key || "Unknown Key"}`) // Handle potentially undefined Key
      .join("\n");

    console.log("\nHere's a list of files in the bucket:");
    console.log(`${contentsList}\n`);
  } catch (err: unknown) {
    console.error("Error listing bucket files:", (err as Error).message);
  }
};

// Checks whether or not the depdencies added to the connected layer can be accessed
// Type the return value as a Lambda result
const checkDependencies = (): APIGatewayProxyResult => {
  try {
    const nodeModulesPath = '/opt/nodejs/node22/node_modules';  // Default path for Lambda layers
    const filesInLayer: string[] = fs.readdirSync(nodeModulesPath);
    console.log('Files in /opt/nodejs/node22/node_modules:', filesInLayer);

    return {
      statusCode: 200,
      body: JSON.stringify({ success: 'Layer can be accessed' }),
    };
  } catch (error: unknown) {
    console.error('Error:', (error as Error).message);
    return {
      statusCode: 500,
      body: JSON.stringify({
        error: 'Failed to access the dependencies from the layer',
        message: (error as Error).message
      }),
    };
  }
}