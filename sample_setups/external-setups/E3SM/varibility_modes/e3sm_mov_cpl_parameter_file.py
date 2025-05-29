import os
import sys
import json

#####################
#basic information
#####################
model_name = 'e3sm.historical.v3-LR.0051'
start_yr = int('1900')
end_yr = int('2014')
num_years = end_yr - start_yr + 1
period = "{:04d}{:02d}-{:04d}{:02d}".format(start_yr,1,end_yr,12)

mip = model_name.split(".")[0]
exp = model_name.split(".")[1]
product = model_name.split(".")[2]
realm = model_name.split(".")[3]
tableId = 'Amon'
case_id = 'v20250131'

seasons   = 'yearly,monthly'.split(",")
frequency = 'mo'

#model 
varModel = 'ts'
#unit conversion (namelist)
ModUnitsAdjust = (True,"subtract",273.15)
test_data_path = 'ts'
test_data_set = [exp]

#reference 
varOBS  = 'ts'
#unit conversion (namelist)
ObsUnitsAdjust = (True,"subtract",273.15)
obs_file = "ts_ref_variability_modes_cpl_catalogue.json"
obs_dic = json.load(open(obs_file))
reference_data_path = 'ts_ref'
reference_data_set  = obs_dic[varOBS]['set']
reference_data_name = obs_dic[varOBS][refset]
reference_data_path = obs_dic[varOBS][refname]['file_path']
osyear = int(str(obs_dic[varOBS][refname]['yymms'])[0:4])
oeyear = int(str(obs_dic[varOBS][refname]['yymme'])[0:4])

variability_mode = "PDO" #NPGO,AMO
eofn_mod = "1" #"2,2"
eofn_obs = "1" #"2,2"

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

# If True, maskout land region thus consider only over ocean
landmask = True

#template for model file
modnames = [ product ]
realization = "*"
modpath = os.path.join(
  'ts',
  '{}.{}.%(model).%(realization).{}.%(variable).{}.nc'.format(mip,exp,tableId,period)
)

#start and end year for analysis
msyear = int(start_yr)
meyear = int(end_yr)

# If True, remove Domain Mean of each time step
RmDomainMean = True

# If True, consider EOF with unit variance
EofScaling = False

# Conduct CBF analysis
CBF = True

# Conduct conventional EOF analysis
ConvEOF = True

# Generate CMEC compliant json
cmec = False

# Update diagnostic file if exist
update_json = False

#results directory structure.
results_dir = os.path.join(
    'pcmdi_diags',
    '%(output_type)',
    'variability_modes',
    '%(mip)',
    '%(exp)',
    case_id,
    '%(variability_mode)',
    '%(reference_data_name)',
)

