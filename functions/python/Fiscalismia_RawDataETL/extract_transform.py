from timedelta_analysis import add_time_analysis_entry
import requests # not in aws runtime
from datetime import datetime
import zoneinfo

def extract_and_transform_to_tsv(
      start_time: int,
      sheet,
      s3_bucket: str,
      timedelta_analysis: list[str],
      s3_client,
      logger
):
    add_time_analysis_entry(timedelta_analysis, start_time, "finalized TSV extraction from Finance sheet")
    return {"status": "Success"}
