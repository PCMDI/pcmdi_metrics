PMP Extremes Metrics

How to run driver:
python pmp_extremes_driver.py -p parameter_file --other_params

This script will produce metrics JSONs and netcdf files (optional) containing block max/min values for temperature and/or precipitation. 

Temperature: metrics in same units as input data. Must have variable "tasmax" or "tasmin"

Precipitation: inputs expected to be kg/m2/s. Converts to mm/day. Variable name must be pr,PRECT, or precip

It is not required to provide a reference dataset

The default JSON output is designed to be cmec compliant - do not need to use CMEC flag.

Data is masked to be over land only (50<=sftlf<=100)

Running over regions:
You can either use a region from a shapefile or provide coordinates.
Shapefile: --shp_path is path to shapefile, --column is the attribute name, --region_name is the name of the region within that attribute. The shapefile cannot have multiple separate features with the same value of "region_name".
Coordinates: --cords A list containing coordinate pairs. The pairs must be listed in consecutive order, as they would occur when walking the perimeter of the bounding shape. Does not need to be a square, but cannot have holes. Eg [[x1,y1],[x1,y2],[x2,y2],[x2,y1]]. --region_name can be provided, or will be listed as "custom".

Time series settings:
dec_mode: "DJF" or "JFD". 
annual_strict: This only matters for rx5day. If true, only use data from within that year in the 5-day means (first mean taken at Jan 5).
drop_incomplete_djf: Don't include data from the first JF and last D in the analysis.




