# CMIP5
# This parameter file goes with sea_ice_parallel_cmip5_sft.py
var = "sic"
# realization=["r1i1p1","r2i1p1","r3i1p1","r4i1p1"]
realization = "*"
msyear = 1988
meyear = 2005
metrics_output_path = (
    "/work/ordonez4/sea_ice/cmip5_" + str(msyear) + "-" + str(meyear) + "/%(case_id)/"
)

ModUnitsAdjust = (True, "multiply", 1e-2)
AreaUnitsAdjust = (True, "multiply", 1e-6)


# OSI-SAF data
reference_data_path_nh = (
    "/p/user_pub/PCMDIobs/obs4MIPs_input/EUMETSAT/OSI-SAF-450-a-3-0/v20231201/*nh*"
)
reference_data_path_sh = (
    "/p/user_pub/PCMDIobs/obs4MIPs_input/EUMETSAT/OSI-SAF-450-a-3-0/v20231201/*sh*"
)
ObsUnitsAdjust = (True, "multiply", 1e-2)
reference_data_set = "OSI-SAF"
osyear = msyear
oeyear = meyear
obs_var = "ice_conc"
ObsAreaUnitsAdjust = (False, 0, 0)
obs_area_template = None  # km2
obs_area_var = None
obs_cell_area = 625
plot = True
netcdf = True
