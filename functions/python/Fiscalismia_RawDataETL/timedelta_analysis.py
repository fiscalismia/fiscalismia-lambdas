import time

def add_time_analysis_entry(timedelta_analysis, start_time, log_msg):
  timedelta_analysis.append(f"{round((time.time_ns() - start_time) / 1_000_000)}ms time passed after [{log_msg}]")

def log_time_analysis(timedelta_analysis, logger, info_log=True):
  if info_log:
    logger.info("Timedelta analysis concluded.", extra={ "timedelta_analysis" : timedelta_analysis })
  logger.debug("Timedelta analysis concluded.", extra={ "timedelta_analysis" : timedelta_analysis })
