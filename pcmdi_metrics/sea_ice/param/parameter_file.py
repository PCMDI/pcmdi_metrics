# CMIP6
# =======
case_id = "cmip6_osi-saf"
test_data_set = [
    "E3SM-1-0",
    "CanESM5",
    "CAS-ESM2-0",
    "GFDL-ESM4",
    "E3SM-2-0",
    "MIROC6",
    "ACCESS-CM2",
    "ACCESS-ESM1-5",
]
realization = "*"
test_data_path = "links_siconc/%(model)/historical/%(realization)/siconc/"
filename_template = "siconc_SImon_%(model)_historical_%(realization)_*_*.nc"
var = "siconc"
msyear = 1981
meyear = 2000
ModUnitsAdjust = (True, "multiply", 1e-2)

area_template = "links_area/%(model)/*.nc"
area_var = "areacello"
AreaUnitsAdjust = (True, "multiply", 1e-6)

metrics_output_path = "demo/%(case_id)/"


# OSI-SAF data
reference_data_path_nh = (
    "/p/user_pub/PCMDIobs/obs4MIPs_input/EUMETSAT/OSI-SAF-450-a-3-0/v20231201/*nh*"
)
reference_data_path_sh = (
    "/p/user_pub/PCMDIobs/obs4MIPs_input/EUMETSAT/OSI-SAF-450-a-3-0/v20231201/*sh*"
)
ObsUnitsAdjust = (True, "multiply", 1e-2)
reference_data_set = "OSI-SAF"
osyear = 1981
oeyear = 2010
obs_var = "ice_conc"
ObsAreaUnitsAdjust = (False, 0, 0)
obs_area_template = None  # km2
obs_area_var = None
obs_cell_area = 625
