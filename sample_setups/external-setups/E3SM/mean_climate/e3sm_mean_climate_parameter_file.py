import os
import sys
import json

#####################
#basic information
#####################
model_name = "e3sm.historical.v3-LR.0051"
start_yr = int('1985')
end_yr = int('2014')
num_years = end_yr - start_yr + 1
period = "{:04d}{:02d}-{:04d}{:02d}".format(start_yr,1,end_yr,12)

mip = model_name.split(".")[0]
exp = model_name.split(".")[1]
product = model_name.split(".")[2]
realm = model_name.split(".")[3]
tableId = 'Amon'
case_id = 'v20250131' 

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

#case id
modver = case_id 

#always turn off
parallel = False

#land/sea mask file (already generated)
generate_sftlf = False
sftlf_filename_template = modpath_lf

# INTERPOLATION OPTIONS
# OPTIONS: '2.5x2.5' or an actual cdms2 grid object
target_grid = '2.5x2.5'
targetGrid = target_grid
target_grid_string = '2p5x2p5'
# OPTIONS: 'regrid2','esmf'
regrid_tool = 'esmf'
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method = 'regrid2'
# OPTIONS: "regrid2","esmf"
regrid_tool_ocn = ''
# OPTIONS: 'linear','conservative', only if tool is esmf
regrid_method_ocn = ( 'conservative' )

#######################################
# DATA LOCATION: MODELS
# ---------------------------------------------
realization = "*"
test_data_set = [ product ]
test_data_path = 'climo'
# Templates for model climatology files
filename_template = '.'.join([
  mip,
  exp,
  '%(model)',
  '%(realization)',
  'Amon',
  '%(variable)',
  period,
  'AC',
  case_id,
  'nc'
])

#observation info
reference_data_path = 'climo_ref'
custom_observations = os.path.join(
   'pcmdi_diags',
   '{}_{}_catalogue.json'.format(
   'climo_ref',
   'mean_climate'))

#load caclulated regions for each variable
regions = json.load(open('regions.json'))

#load predefined region information
regions_specs = json.load(open('regions_specs.json'))
for key in regions_specs.keys():
  if "domain" in regions_specs[key].keys():
    if "latitude" in regions_specs[key]['domain'].keys():
      regions_specs[key]['domain']['latitude'] = tuple(
             regions_specs[key]['domain']['latitude']
      )
    if "longitude" in regions_specs[key]['domain'].keys():
      regions_specs[key]['domain']['longitude'] = tuple(
             regions_specs[key]['domain']['longitude']
      )

#######################################
# DATA LOCATION: METRICS OUTPUT
metrics_output_path = os.path.join(
    'pcmdi_diags',
    'metrics_results',
    'mean_climate',
     mip,
     exp,
    '%(case_id)'
)

############################################################
# DATA LOCATION: INTERPOLATED MODELS' CLIMATOLOGIES
diagnostics_output_path= os.path.join(
    'pcmdi_diags',
    'diagnostic_results',
    'mean_climate',
     mip,
     exp,
    '%(case_id)'
)
test_clims_interpolated_output = diagnostics_output_path

