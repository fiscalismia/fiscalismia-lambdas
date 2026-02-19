import pandas as pd
from io import BytesIO
from timedelta_analysis import add_time_analysis_entry
import requests # not in aws runtime

def download_csv(
      start_time: int,
      timestamp: str,
      sheet_url: str,
      s3_bucket: str,
      timedelta_analysis: list[str],
      s3_client,
      logger
) -> pd.DataFrame:
    """
    Queries Google Sheets via HTTP Request to download a CSV export into memory.
    - Persists sheet with timestamp to s3 into s3://fiscalismia-raw-data-etl-storage/tmp/
    - Uses pandas with c engine for
    - Returns the parsed DataFrame
    """
    # Download the spreadsheet from google docs into memory
    response = requests.get(sheet_url, stream=True, timeout=(3, 10)) # (3s connect timeout, 10s read timeout)
    if response.status_code != 200:
      raise RuntimeError(f"Failed to download the sheet. HTTP status: {response.status_code}")
    add_time_analysis_entry(timedelta_analysis, start_time, "request CSV file via URL")

    raw_bytes = response.content
    s3_buffer = BytesIO(raw_bytes)
    csv_buffer = BytesIO(raw_bytes)

    # Persist raw bytes to S3 as timestamped backup
    s3_key = f"tmp/{timestamp}-Fiscalismia-Datasource.csv"
    add_time_analysis_entry(timedelta_analysis, start_time, "load CSV file into memory")
    s3_client.upload_fileobj(s3_buffer, s3_bucket, s3_key)
    logger.debug(f"CSV persisted to s3://{s3_bucket}/{s3_key}")
    add_time_analysis_entry(timedelta_analysis, start_time, "persist CSV file to s3 /tmp")

    # Parse CSV into DataFrame via pyarrow engine
    # See https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html
    # See https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html
    csv: pd.DataFrame = pd.read_csv(
        csv_buffer,
        sep=",",          # explicit comma delimiter
        header=None,      # no header row — treat all rows as data
        na_filter=False,  # skip NA detection for performance
        dtype=str,        # preserve all raw cell values as strings
        engine="c",       # pyarrow engine is too large of a dependency
        low_memory=False  # Internally process the file in chunks, resulting in lower memory use while parsing
    )
    add_time_analysis_entry(timedelta_analysis, start_time, "read CSV via pandas C engine")
    logger.debug(f"Loaded CSV into memory with pandas pyarrow engine. Shape: {csv.shape}")
    return csv
