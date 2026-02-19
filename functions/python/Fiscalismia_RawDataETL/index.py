import json
import boto3
import time
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities import parameters
from download_xlsx import download_xlsx
from download_csv import download_csv
from clean_sheet_url import clean_sheet_url
from timedelta_analysis import add_time_analysis_entry, log_time_analysis
from extract_transform import extract_and_transform_to_tsv
s3_client = boto3.client('s3')
s3_bucket = 'fiscalismia-raw-data-etl-storage'
logger = Logger(service="Fiscalismia_RawDataETL")

def authenticate_request(body, headers):
  contentLength = int(headers.get('Content-Length', 0))
  authorization = headers.get('authorization', None)
  requestIp = headers.get('X-Forwarded-For', None)

  logger.info("Request received", extra={"ip": requestIp})

  secret = parameters.get_secret(
    "arn:aws:secretsmanager:eu-central-1:010928217051:secret:/api/fiscalismia/API_GW_SECRET_KEY-4AjIFN",
    transform="json"
  )
  secret_api_key = secret.get("API_GW_SECRET_KEY", None)
  # block access if payload is sent
  if body or contentLength > 0:
    return {
      "statusCode": 422,
      "body": json.dumps({"message": "No payload expected. Request body should be empty."})
    }
  # block access if authorization header does not include the API TOKEN
  if authorization == None or secret_api_key == None or authorization != secret_api_key:
    return {
      "statusCode": 403,
      "body": json.dumps({"message": "Invalid Authorization header."})
    }
  # Everything is fine. Proceed
  logger.info("Request authenticated successfully")
  return {"statusCode": 200}

def log_debug_info(event, headers, context, info_log=True):
  extractedEventKeys = {
    "HTTP" : event.get('httpMethod', None),
    "Host" : headers.get("Host", None),
    "path" : event.get('path', None),
    "contentLength" : int(headers.get('Content-Length', 0)),
    "X-Forwarded-For" : headers.get('X-Forwarded-For', None),
    "User-Agent" : headers.get('User-Agent', None),
    "queryStringParameters" : event.get('queryStringParameters', None),
    "body" : event.get("body", None)
  }
  if info_log:
    logger.info("Debug info extracted", extra={"eventKeys": extractedEventKeys})
  logger.debug("Debug info extracted", extra={"eventKeys": extractedEventKeys})

def lambda_handler(event, context):
  timedelta_analysis = []
  start_time = time.time_ns()
  add_time_analysis_entry(timedelta_analysis, start_time, "function invocation")
  body = event.get("body", None)
  headers = event.get("headers", None)
  log_debug_info(event, headers, context)
  auth_response = authenticate_request(body, headers)
  if auth_response.get("statusCode", None) != 200:
    return auth_response
  add_time_analysis_entry(timedelta_analysis, start_time, "request authentication")
  try:
    secret = parameters.get_secret(
      "arn:aws:secretsmanager:eu-central-1:010928217051:secret:/google/sheets/fiscalismia-datasource-url-k38OGm",
      transform="json"
    )
    sheet_url = secret["GOOGLE_SHEETS_URL"]
    # Verify spreadsheet url is not malformed
    # Download the spreadsheet from google docs into memory
    sheet_url = clean_sheet_url(sheet_url, logger, "xlsx")
    sheet = download_xlsx(start_time, sheet_url, s3_bucket, timedelta_analysis, s3_client, logger)
    sheet_url = clean_sheet_url(sheet_url, logger, "csv")
    sheet = download_csv(start_time, sheet_url, s3_bucket, timedelta_analysis, s3_client, logger)
    sheet_sanity_check = extract_and_transform_to_tsv(start_time, sheet, s3_bucket, timedelta_analysis, s3_client, logger)

    # log timedeltas for performance monitoring
    logger.info("finalized extract transform loading operation")
    log_time_analysis(timedelta_analysis, logger)
    return {
      "statusCode": 200,
      "body": sheet_sanity_check
    }
  except RuntimeError as e:
    logger.error("Runtime error during ETL", extra={"error": str(e)})
    return {
      "statusCode": 500,
      "body": json.dumps({"error": str(e)})
    }
  except Exception as e:
    logger.error("Unexpected error during ETL", extra={"error": str(e)})
    return {
        "statusCode": 500,
        "body": json.dumps({"error": str(e)})
    }
