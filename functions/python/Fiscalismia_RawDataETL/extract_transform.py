import json
from timedelta_analysis import add_time_analysis_entry

def extract_and_transform_to_tsv(
  start_time: int,
  sheet,
  s3_bucket: str,
  timedelta_analysis: list[str],
  s3_client,
  logger
):
  row_count = sheet.shape[0]
  col_count = int(sheet.shape[1])
  output = json.dumps(
  {
        "size": f"{sheet.size} bytes",
        "rows": row_count,
        "columns": col_count,
        "header": sheet.iloc[3, :].to_dict(),
        "tail": sheet.tail(1).astype(str).to_dict(orient="records"),
  })
  add_time_analysis_entry(timedelta_analysis, start_time, "finalized TSV extraction from Finance sheet")
  return output
