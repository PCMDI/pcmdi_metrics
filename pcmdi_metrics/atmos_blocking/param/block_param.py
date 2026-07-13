# Path pattern for input height data files
FILE_GLOB = "/share/data1/Students/jfields/E3SM/zg_day_*_*.nc"

# Processing configuration
PRESSURE_LEVEL = 500
START_DATE = "1950-01-01"
END_DATE = "2014-12-31"

# Output configuration
OUTPUT_DIR = "/share/data1/Students/jfields/block_data/in_progress"
STITCHED_OUT_NAME = "block_tag.stitched.nc"
CLEANUP_TEMP = True
