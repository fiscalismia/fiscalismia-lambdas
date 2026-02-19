import json
import pandas as pd
from openpyxl import Workbook
from openpyxl import load_workbook

from io import BytesIO
from timedelta_analysis import add_time_analysis_entry
import requests # not in aws runtime
from datetime import datetime
import zoneinfo

def download_sheet(
      start_time: int,
      sheet_url: str,
      s3_bucket: str,
      timedelta_analysis: list[str],
      s3_client,
      logger
):
    # Download the spreadsheet from google docs into memory
    response = requests.get(sheet_url, stream=True, timeout=(3, 10)) # (3s connect timeout, 10s read timeout)
    if response.status_code != 200:
      raise RuntimeError(f"Failed to download the sheet. HTTP status: {response.status_code}")
    add_time_analysis_entry(timedelta_analysis, start_time, "request spreadsheet via URL")
    if response.status_code != 200:
      return {
        "statusCode": 500,
        "body": json.dumps({"error": "Failed to download the sheet"})
      }
    s3_buffer = BytesIO(response.content)
    workbook_buffer = BytesIO(response.content)

    # Load temporary file as binary object into memory for S3 backup
    berlin_tz = zoneinfo.ZoneInfo("Europe/Berlin")
    timestamp = datetime.now(tz=berlin_tz).strftime("%Y-%m-%d-%H-%M-%S")
    s3_key = f"tmp/{timestamp}-Fiscalismia-Datasource.xlsx"
    add_time_analysis_entry(timedelta_analysis, start_time, "load sheet into memory temp file")
    s3_client.upload_fileobj(s3_buffer, s3_bucket, s3_key)
    logger.debug(f"Worksheet persisted to s3://{s3_bucket}/{s3_key}")
    add_time_analysis_entry(timedelta_analysis, start_time, "persist temp file to s3")

    # Load all sheets into DataFrames via calamine engine
    sheets: dict[str, pd.DataFrame] = pd.read_excel(
        workbook_buffer,
        sheet_name='Finances',   # use None to read all sheets
        engine="calamine", # fastest engine for xlsx reading
        header=0,          # first row as column headers
        na_filter=False,   # skip NA detection for performance
        dtype=object,      # preserve raw cell values, no type inference
    )
    add_time_analysis_entry(timedelta_analysis, start_time, "loaded workbook into memory")
    logger.debug("Loaded sheet into memory with pandas and calamine engine.")

    return sheets
