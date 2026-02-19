from openpyxl import Workbook
from openpyxl import load_workbook
from timedelta_analysis import add_time_analysis_entry
import requests # not in aws runtime
from datetime import datetime
import zoneinfo

def extract_and_transform_to_tsv(
      start_time: int,
      workbook: Workbook,
      s3_bucket: str,
      timedelta_analysis: list[str],
      s3_client,
      logger
):
    add_time_analysis_entry(timedelta_analysis, start_time, "request spreadsheet via URL")

    return workbook
