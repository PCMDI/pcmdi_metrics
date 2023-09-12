


#====tasmax====
vars = ["tasmax"]
ModUnitsAdjust=(True,"subtract",273,"C")

#metrics_output_path = "test_py_ns_100_tasmax_MRI_2"
#metrics_output_path = "test_ce_st_100_tasmax_MRI"
metrics_output_path = "test_ce_ns_100_tasmax_MRI_2"


#===pr====
#vars = ["pr"]
#ModUnitsAdjust=(True,"multiply",86400,"mm/day")
#metrics_output_path = "test_py_ns_100_pr_MRI"
#metrics_output_path = "test_ce_st_100_pr_MRI"
#metrics_output_path = "test_ce_ns_100_pr_MRI"

# Covariate - comment out to do nonstationary
covariate = "mole_fraction_of_carbon_dioxide_in_air"
covariate_path = "/home/ordonez4/git/pcmdi_metrics/pcmdi_metrics/extremes/co2_annual_1900-1999.nc"

# Don't need to edit below here for 100 year runs
test_data_set=["MRI-ESM2-0"]
realization = ["r1i1p1f1"]
test_data_path = "/p/user_pub/xclim/CMIP6/CMIP/1pctCO2/atmos/day/%(variable)"
filename_template = "CMIP6.CMIP.1pctCO2.*.%(model).%(realization).day.%(variable).atmos.*.v????????.0000000.0.xml"
sftlf_filename_template = "/p/css03/esgf_publish/CMIP6/CMIP/*/%(model)/piControl/r1i1p1f1/fx/sftlf/gn/v????????/sftlf_fx_%(model)_piControl_r1i1p1f1_gn.nc"

#case_id = ver
dec_mode="DJF"
annual_strict = False
drop_incomplete_djf = False
regrid=False
plots=False
generate_sftlf = False
msyear = 1900
meyear = 1999
return_period = 20


#year_range = [1900,1930]
#coords="[[0,100],[100,100],[100,0],[0,0]]"
#shp_path = "test_can_geom.shp"
#column = "SOVEREIGNT"
#region_name = "Canada"

#reference_data_path = "test_data/fake_tasmax_obs_19800101-19991231.nc"
#reference_data_set = "fake_tasmax"
#reference_sftlf_template = "/p/css03/esgf_publish/CMIP6/CMIP/MRI/MRI-ESM2-0/historical/r1i1p1f1/fx/sftlf/gn/v20190603/sftlf_fx_MRI-ESM2-0_historical_r1i1p1f1_gn.nc"
#osyear = 1950
#oeyear = 1999
