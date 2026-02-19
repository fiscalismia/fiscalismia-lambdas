global_sheet_id = 887527210
def clean_sheet_url(sheet_url, logger, export_type):
  if not sheet_url :
    raise RuntimeError("Spreadsheet url from secret manager missing.")
  if "docs.google.com/spreadsheets" not in sheet_url:
    raise RuntimeError(f"Spreadsheet url from secret manager malformed: {sheet_url}")

  if f"pub?output={export_type}" in sheet_url or f"export?format={export_type}" in sheet_url:
    pass
    logger.info(f"sheet_url formed correctly for {export_type}")
  elif "/edit" in sheet_url:
    sheet_url = sheet_url.split("/edit")[0] + f"/export?format={export_type}&gid={global_sheet_id}"
    logger.info(f"sheet_url edit rewritten to format={export_type}")
  elif "/view" in sheet_url:
    sheet_url = sheet_url.split("/view")[0] + f"/export?format={export_type}&gid={global_sheet_id}"
    logger.info(f"sheet_url view rewritten to format={export_type}")
  elif "/pubhtml" in sheet_url:
    sheet_url = sheet_url.split("/pubhtml")[0] + f"/pub?output={export_type}&gid={global_sheet_id}"
    logger.info(f"sheet_url pubhtml rewritten to pub?output={export_type}")
  else:
    sheet_url = '/'.join(sheet_url.split("/")[:-1]) + f"/export?format={export_type}&gid={global_sheet_id}"
    logger.info(f"sheet_url suffix not identifiable. Hardcoded to /export?format={export_type}&gid={global_sheet_id}")

  return sheet_url