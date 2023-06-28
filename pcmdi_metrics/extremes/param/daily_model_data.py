

vars = ["pr"]

test_data_set = ["MRI-ESM2-0"]
#test_data_set = ["MIROC6"]
realization = ["r1i1p1f1"]
test_data_path = "/p/css03/esgf_publish/CMIP6/CMIP/*/%(model)/1pctCO2/%(realization)/day/%(variable)/*/*/"
filename_template = "%(variable)_day_%(model)_1pctCO2_%(realization)_gn_19500101-19991231.nc"
sftlf_filename_template = "/p/css03/esgf_publish/CMIP6/CMIP/*/%(model)/historical/r1i1p1f1/fx/sftlf/*/*/sftlf_fx_%(model)_historical_r1i1p1f1_*.nc"

metrics_output_path = "debug_nc/"

#test_data_set = ["MIROC6","GISS-E2-1-G"]
#test_data_set = ["GISS-E2-1-G"]
#test_data_set = ["CESM2"]
#realization = ["r1i1p1f1"]
#test_data_path = "/p/user_pub/xclim/CMIP6/CMIP/historical/atmos/day/%(variable)"
#filename_template = "CMIP6.CMIP.historical.*.%(model).%(realization).day.%(variable).atmos.*.v????????.0000000.0.xml"
#sftlf_filename_template = "/p/css03/esgf_publish/CMIP6/CMIP/*/%(model)/piControl/r1i1p1f1/fx/sftlf/gn/v????????/sftlf_fx_%(model)_piControl_r1i1p1f1_gn.nc"

#case_id = ver
dec_mode="DJF"
annual_strict = False
drop_incomplete_djf = True
nc_out=True
regrid=False
plots=False
generate_sftlf = False

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