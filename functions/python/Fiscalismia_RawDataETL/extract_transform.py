import json
import pandas as pd
from io import BytesIO
from timedelta_analysis import add_time_analysis_entry
from ddl_schema import (
  HEADER_ROW,
  DATA_START_ROW,
  TABLE_VAR_EXPENSES,
  TABLE_FIXED_COSTS,
  TABLE_INVESTMENTS,
  TABLE_INCOME,
  TABLE_NEW_FOOD_ITEMS,
)

def _extract_trivial_table(sheet: pd.DataFrame, table_def: dict) -> pd.DataFrame:
  """
  - Extract a subtable slice using iloc.
  - Drops all empty rows
  - strips all values of extra whitespace
  Rows whose first column value appears in skip_markers are dropped.
  """
  col_slice = table_def["col_slice"]
  skip_markers = table_def.get("skip_markers", None)

  # Slices the sheet into its subtable range
  data_frame = sheet.iloc[DATA_START_ROW:, col_slice].copy()
  # Drops all empty rows from dataframe
  data_frame = data_frame.dropna(how="all")

  # Get all rows (:) from FIRST column (0) and perform vectorized strip operation
  first_col = data_frame.iloc[:, 0].astype(str).str.strip()
  # Drops any rows whose first column is marked to be skipped
  data_frame = data_frame[~first_col.isin(skip_markers)]
  # Drops any rows that are null, empty
  data_frame = data_frame[first_col.notna() & (first_col != "")]

  data_frame.columns = table_def["col_names"]
  return data_frame.reset_index(drop=True)

def _extract_multisection_table(sheet: pd.DataFrame, table_def: dict, logger) -> pd.DataFrame:
  """
  Extract a multi-section table where "Date: DD.MM.YYYY - DD.MM.YYYY" group-headers are present
  The parsed date range is broadcast to every following data row as
  effective_date / expiration_date until the next Date row is encountered.
  """
  col_slice = table_def["col_slice"]
  skip_markers = table_def.get("skip_markers", None)
  date_marker = table_def["date_marker"]
  date_col_offset = table_def["date_value_col_offset"]

  # Slices the sheet into its subtable range
  raw_data = sheet.iloc[DATA_START_ROW:, col_slice].copy()
  # Drops all empty rows from dataframe
  raw_data = raw_data.dropna(how="all")
  # resets indices to 0 and drops stale references to any dropped rows
  raw_data = raw_data.reset_index(drop=True)

  records = []
  current_effective = None
  current_expiration = None

  # INFO: itertuples might be a more performant operation https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.itertuples.html#pandas.DataFrame.itertuples
  for _, row in raw_data.iterrows():
    first_val = str(row.iloc[0]).strip()

    if first_val == date_marker:
      # Parse "DD.MM.YYYY - DD.MM.YYYY" from the adjacent column
      date_string = str(row.iloc[date_col_offset]).strip()
      parts = [p.strip() for p in date_string.split("-", 1)]
      current_effective = parts[0] if len(parts) > 0 else None
      current_expiration = parts[1] if len(parts) > 1 else None
      logger.info(f"Date String in col slice {col_slice} with effective {current_effective} and expiration {current_expiration}")
      continue

    if first_val in skip_markers or first_val in {"", "nan"}:
      continue

    record = row.tolist() + [current_effective, current_expiration]
    records.append(record)

  output_cols = table_def["col_names"] + table_def.get("derived_col_names", [])
  return pd.DataFrame(records, columns=output_cols)


def load_tables_from_sheet(sheet: pd.DataFrame, logger) -> dict[str, pd.DataFrame]:
  """
  Extract all five Finance tables from the raw sheet using iloc-based column
  slices defined in ddl_schema.py.

  Returns a dict keyed by table name:
    "variable_expenses", "fixed_costs", "investments", "income", "food_items"
  """
  trivial_table = {
    "variable_expenses": TABLE_VAR_EXPENSES,
    "investments":       TABLE_INVESTMENTS,
    "food_items":        TABLE_NEW_FOOD_ITEMS,
  }
  multisection_table = {
    "fixed_costs": TABLE_FIXED_COSTS,
    "income":      TABLE_INCOME,
  }

  result = {}
  for name, table_def in trivial_table.items():
    result[name] = _extract_trivial_table(sheet, table_def)

  for name, table_def in multisection_table.items():
    result[name] = _extract_multisection_table(sheet, table_def, logger)

  return result

def extract_and_transform_to_tsv(
  start_time: int,
  timestamp: str,
  sheet,
  s3_bucket: str,
  timedelta_analysis: list[str],
  s3_client,
  logger
) -> list[str]:
  """
  Extracts subtable ranges from main finance sheet, serializing each
  as a TSV file, uploads them to the specified S3 bucket under the
  ``transformed/`` prefix, and returns short-lived presigned URLs.

  Returns:
      A list of presigned S3 URLs (one per extracted table)
  """
  row_count = sheet.shape[0]
  col_count = int(sheet.shape[1])
  debug_output = json.dumps(
  {
    "size": f"{sheet.size} bytes",
    "rows": row_count,
    "columns": col_count,
    "header": sheet.iloc[HEADER_ROW, :].to_dict(),
    "tail": sheet.tail(1).astype(str).to_dict(orient="records"),
  })
  logger.debug("Running sanity check on Finance sheet", extra={"sanity_check": debug_output})

  tables = load_tables_from_sheet(sheet, logger)
  s3_presigned_urls: list[str] = []
  for table_name, df in tables.items():
    file_name = f"{timestamp}-{table_name}.tsv"
    s3_key = f"transformed/{file_name}"
    logger.debug(f"Extracted table '{table_name}'", extra={"shape": str(df.shape)})
    s3_buffer = BytesIO(df.to_csv(sep="\t", index=False).encode("utf-8"))
    s3_client.upload_fileobj(s3_buffer, s3_bucket, s3_key)
    s3_object_uri = f"{s3_bucket}/{s3_key}"
    logger.debug(f"TSV persisted to s3://{s3_object_uri}")
    url = s3_client.generate_presigned_url(
      ClientMethod='get_object',
      Params={
          'Bucket': s3_bucket,
          'Key': s3_key
      },
      ExpiresIn=300
    )
    s3_presigned_urls.append(url)

  add_time_analysis_entry(timedelta_analysis, start_time, "finalized TSV extraction from Finance sheet")
  return s3_presigned_urls
