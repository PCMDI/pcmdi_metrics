import datetime
import os

ver = datetime.datetime.now().strftime("v%Y%m%d")

#test_data_set = ["MRI-ESM2-0","INM-CM5-0"]
test_data_set = ["MRI-ESM2-0"]
realization = ["r1i1p1f1"]
vars = ["tasmax"]
test_data_path = "/p/css03/esgf_publish/CMIP6/CMIP/*/%(model)/1pctCO2/r1i1p1f1/day/%(variable)/*/*/"
filename_template = "%(variable)_day_%(model)_1pctCO2_r1i1p1f1_gn_19500101-19991231.nc"
sftlf_filename_template = "/p/css03/esgf_publish/CMIP6/CMIP/*/%(model)/historical/r1i1p1f1/fx/sftlf/*/*/sftlf_fx_%(model)_historical_r1i1p1f1_*.nc"
metrics_output_path = "test_obs/"
#case_id = ver
dec_mode="JFD"
annual_strict = True
nc_out=True
regrid=False

#year_range = [1900,1930]
#coords="[[0,100],[100,100],[100,0],[0,0]]"
#shp_path = "test_can_geom.shp"
#column = "SOVEREIGNT"
#region_name = "Canada"

reference_data_path = "test_data/fake_tasmax_obs_19800101-19991231.nc"
reference_data_set = "fake_tasmax"
reference_sftlf_template = "/p/css03/esgf_publish/CMIP6/CMIP/MRI/MRI-ESM2-0/historical/r1i1p1f1/fx/sftlf/gn/v20190603/sftlf_fx_MRI-ESM2-0_historical_r1i1p1f1_gn.nc"
