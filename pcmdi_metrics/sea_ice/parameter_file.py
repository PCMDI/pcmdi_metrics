# CMIP5
#=========
# Model settings
#test_data_set=["ACCESS1-3","GISS-E2-H","NorESM1-M"]
#test_data_set=["ACCESS1-3"]
#realization=["*"]
#test_data_path = "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/v20231104/cmip5/historical/seaIce/mon/sic/"
#filename_template= "cmip5.historical.%(model).%(realization).mon.sic.xml"
#var="sic"
#msyear=1981
#meyear=2010
#ModUnitsAdjust=(True,"multiply",1e-2)

# Model area file
#area_template="/p/user_pub/hoang1-backups/ARCHIVE/ivanova2/IceMetrics/CMIP5/AREACELLO/areacello_fx_%(model)_historical_r0i0p0.nc"
#area_var = "areacello"
#AreaUnitsAdjust = (True, "multiply", 1e-6)

# CMIP6
#=======
test_data_set=["E3SM-1-0","MIROC6"]
realization="*"
test_data_path="/p/user_pub/cmip/CMIP6/CMIP/*/%(model)/historical/%(realization)/SImon/siconc/*/*/"
filename_template="siconc_SImon_%(model)_historical_%(realization)_*_*.nc"
var="siconc"
msyear=1981
meyear=2010
ModUnitsAdjust=(True,"multiply",1e-2)

area_template="/p/css03/esgf_publish/CMIP6/CMIP/*/%(model)/historical/%(realization)/fx/areacella/*/*/areacella_fx_%(model)_historical_%(realization)_*.nc"
area_var="areacella"
AreaUnitsAdjust=(True,"multiply",1e-6)


# Reference is hard coded currently so this is a placeholder

#ObsUnitsAdjust=(True,"multiply",1e-2)
#reference_data_set=None
#osyear=1981
#oeyear=2010
#obsvar=""