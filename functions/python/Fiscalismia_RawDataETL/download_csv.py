import json
import pandas as pd
from io import BytesIO
from timedelta_analysis import add_time_analysis_entry
import requests # not in aws runtime
from datetime import datetime
import zoneinfo

def download_csv(
      start_time: int,
      sheet_url: str,
      s3_bucket: str,
      timedelta_analysis: list[str],
      s3_client,
      logger
):
    """
    Queries Google Sheets via HTTP Request to download sheet into memory.
    - Persists sheet with timestamp to s3 into s3://fiscalismia-raw-data-etl-storage/tmp/
    - Uses pandas with calamine engine for fast and efficient parsing
    - Extracts and returns the [Finances] sheet from the workbook
    """
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
    # See https://pandas.pydata.org/docs/reference/api/pandas.read_excel.html
    # See https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html
    sheets: dict[str, pd.DataFrame] = pd.read_excel(
        workbook_buffer,
        sheet_name=None,   # use None to read all sheets
        engine="calamine", # fastest engine for xlsx reading
        header=None,       # row to use as column headers
        na_filter=False,   # skip NA detection for performance
        dtype=str,         # use object to preserve raw cell values
    )
    add_time_analysis_entry(timedelta_analysis, start_time, "loaded workbook into memory")
    logger.debug("Loaded sheet into memory with pandas and calamine engine.")
    sheet_names = list(sheets.keys())
    if 'Finances' not in sheet_names:
      raise RuntimeError(f"In memory workbook is missing [Finances] sheet.")
    return sheets.get('Finances')
