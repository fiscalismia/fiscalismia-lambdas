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


def _extract_simple_table(sheet: pd.DataFrame, table_def: dict) -> pd.DataFrame:
  """
  Extract a single contiguous table block using iloc.
  Rows whose first column value appears in skip_markers are dropped.
  """
  col_slice = table_def["col_slice"]
  skip_markers = table_def.get("skip_markers", set())

  data = sheet.iloc[DATA_START_ROW:, col_slice].copy()
  data = data.dropna(how="all")

  # Drop sub-header / separator / total rows by checking the first column
  first_col = data.iloc[:, 0].astype(str).str.strip()
  data = data[~first_col.isin(skip_markers)]
  data = data[first_col.notna() & (first_col != "") & (first_col != "nan")]

  data.columns = table_def["col_names"]
  return data.reset_index(drop=True)


def _extract_multisection_table(sheet: pd.DataFrame, table_def: dict) -> pd.DataFrame:
  """
  Extract a multi-section table where "Date: X - Y" group-header rows are
  embedded in the data area (used by TABLE_FIXED_COSTS and TABLE_INCOME).
  The parsed date range is broadcast to every following data row as
  effective_date / expiration_date until the next Date row is encountered.
  """
  col_slice = table_def["col_slice"]
  skip_markers = table_def.get("skip_markers", set())
  date_marker = table_def["date_marker"]
  date_col_offset = table_def["date_value_col_offset"]

  raw = sheet.iloc[DATA_START_ROW:, col_slice].copy()
  raw = raw.dropna(how="all")
  raw = raw.reset_index(drop=True)

  records = []
  current_effective = None
  current_expiration = None

  # INFO: itertuples might be a more performant operation https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.itertuples.html#pandas.DataFrame.itertuples
  for _, row in raw.iterrows():
    first_val = str(row.iloc[0]).strip()

    if first_val == date_marker:
      # Parse "DD.MM.YYYY - DD.MM.YYYY" from the adjacent column
      date_string = str(row.iloc[date_col_offset]).strip()
      parts = [p.strip() for p in date_string.split("-", 1)]
      current_effective = parts[0] if len(parts) > 0 else None
      current_expiration = parts[1] if len(parts) > 1 else None
      continue

    if first_val in skip_markers or first_val in {"", "nan"}:
      continue

    record = row.tolist() + [current_effective, current_expiration]
    records.append(record)

  output_cols = table_def["col_names"] + table_def.get("derived_col_names", [])
  return pd.DataFrame(records, columns=output_cols)


def load_tables_from_sheet(sheet: pd.DataFrame) -> dict[str, pd.DataFrame]:
  """
  Extract all five Finance tables from the raw sheet using iloc-based column
  slices defined in ddl_schema.py.

  Returns a dict keyed by table name:
    "variable_expenses", "fixed_costs", "investments", "income", "food_items"
  """
  simple_tables = {
    "variable_expenses": TABLE_VAR_EXPENSES,
    "investments":       TABLE_INVESTMENTS,
    "food_items":        TABLE_NEW_FOOD_ITEMS,
  }
  multisection_tables = {
    "fixed_costs": TABLE_FIXED_COSTS,
    "income":      TABLE_INCOME,
  }

  result = {}
  for name, table_def in simple_tables.items():
    result[name] = _extract_simple_table(sheet, table_def)

  for name, table_def in multisection_tables.items():
    result[name] = _extract_multisection_table(sheet, table_def)

  return result

def extract_and_transform_to_tsv(
  start_time: int,
  timestamp: str,
  sheet,
  s3_bucket: str,
  timedelta_analysis: list[str],
  s3_client,
  logger
):
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

  tables = load_tables_from_sheet(sheet)
  s3_object_uris = []
  for table_name, df in tables.items():
    file_name = f"{timestamp}-{table_name}.tsv"
    s3_key = f"transformed/{file_name}"
    logger.debug(f"Extracted table '{table_name}'", extra={"shape": str(df.shape)})
    s3_buffer = BytesIO(df.to_csv(sep="\t", index=False).encode("utf-8"))
    s3_client.upload_fileobj(s3_buffer, s3_bucket, s3_key)
    s3_object_uri = {s3_bucket}/{s3_key}
    logger.info(f"TSV persisted to s3://{s3_object_uri}")
    s3_object_uris.append(s3_object_uri)

  add_time_analysis_entry(timedelta_analysis, start_time, "finalized TSV extraction from Finance sheet")
  return s3_object_uris
