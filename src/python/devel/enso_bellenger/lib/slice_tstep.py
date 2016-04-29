def tstep_range(start, end, step):
  while start < end and start + step <= end:
    yield start
    start += step
