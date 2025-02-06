import os
import sys
import json

#####################
#basic information
#####################
model_name = 'e3sm.historical.v3-LR.0051'
start_yr = int('1980')
end_yr = int('2015')
num_years = end_yr - start_yr + 1
period = "{:04d}{:02d}-{:04d}{:02d}".format(start_yr,1,end_yr,12)

mip = model_name.split(".")[0]
exp = model_name.split(".")[1]
product = model_name.split(".")[2]
realm = model_name.split(".")[3]

##############################################
#Configuration shared with pcmdi diagnostics
##############################################
# Record NetCDF output
nc_out_obs = True
nc_out_model = True
if nc_out_model or nc_out_obs:
  ext = ".nc"
else:
  ext = ".xml"
user_notes = 'Provenance and results'
debug = False

# Generate plots
plot_model = True
plot_obs = True # optional

# Additional settings
run_type = 'model_vs_obs'
figure_format = 'png'

# Save interpolated model climatology ?
save_test_clims = True

# Save Metrics Results in Single File ?
# option: 'y' or 'n', set to 'n' as we
# run pcmdi for each variable separately
metrics_in_single_file = 'n'

# customize land/sea mask values
regions_values = {"land":100.,"ocean":0.}

#setup template for land/sea mask (fixed)
modpath_lf = os.path.join(
    'fixed',
    'sftlf.%(model).nc'
)

############################################
#setup specific for mean climate metrics
###########################################
#parameter setup specific for enso metrics
###########################################
modnames = [ product ]
realization = realm
modpath = os.path.join(
  'ts',
  '{}.{}.%(model).%(realization).{}.%(variable).{}.nc'.format(mip,exp,'Amon',period)
)

#observation/reference file catalogue
obs_cmor = True
obs_cmor_path = './'
obs_catalogue = 'obs_catalogue.json'

#land/sea mask for obs/reference model
reference_data_lf_path = json.load(open('obs_landmask.json'))

# METRICS COLLECTION (set in namelist, and main driver)
# metricsCollection = ENSO_perf  # ENSO_perf, ENSO_tel, ENSO_proc

# OUTPUT
results_dir = os.path.join(
    'pcmdi_diags',
    '%(output_type)',
    'enso_metric',
    '%(mip)',
    '%(exp)',
    'v20250131',
    '%(metricsCollection)',
)

json_name = "%(mip)_%(exp)_%(metricsCollection)_v20250131_%(model)_%(realization)"

netcdf_name = json_name

