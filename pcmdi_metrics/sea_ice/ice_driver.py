import xarray as xr
import xcdat as xc
import numpy as np
import matplotlib.pyplot as plt
import glob
import json
import os


from pcmdi_metrics.mean_climate.lib import compute_statistics

def rms_t(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Temporal Mean Square Error",
            "Abstract": "Compute Temporal Mean Square Error",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    ds = dm.copy(deep=True)
    ds["diff_square"] = ((dm[var] - do[var]) ** 2) / len(dm["time"])
    stat = ds["diff_square"].data
    return stat

def rms_model(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Square Error",
            "Abstract": "Compute Mean Square Error",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    ds = dm.copy(deep=True)
    ds["diff_square"] = ((dm[var] - do[var]) ** 2)
    stat = ds["diff_square"].data
    return stat

parser = create_sea_ice_parser.create_sea_ice_parser()
parameter = parser.get_parameter(argparse_vals_only=False)

# Parameters
# I/O settings
case_id = parameter.case_id
model_list = parameter.test_data_set
realization = parameter.realization
variable_list = parameter.vars
filename_template = parameter.filename_template
test_data_path = parameter.test_data_path
reference_data_path = parameter.reference_data_path
reference_data_set = parameter.reference_data_set
reference_sftlf_template = parameter.reference_sftlf_template
metrics_output_path = parameter.metrics_output_path
area_template = parameter.grid_area
ModUnitsAdjust = parameter.ModUnitsAdjust
ObsUnitsAdjust = parameter.ObsUnitsAdjust
plots = parameter.plots
msyear = parameter.msyear
meyear = parameter.meyear
osyear = parameter.osyear
oeyear = parameter.oeyear


# Verifying output directory
metrics_output_path = utilities.verify_output_path(metrics_output_path, case_id)

if isinstance(reference_data_set, list):
    # Fix a command line issue
    reference_data_set = reference_data_set[0]

# Verify years
ok_mod = utilities.verify_years(
    msyear,
    meyear,
    msg="Error: Model msyear and meyear must both be set or both be None (unset).",
)
ok_obs = utilities.verify_years(
    osyear,
    oeyear,
    msg="Error: Obs osyear and oeyear must both be set or both be None (unset).",
)

# Initialize output.json file
meta = metadata.MetadataFile(metrics_output_path)

# Initialize other directories
nc_dir = os.path.join(metrics_output_path, "netcdf")
os.makedirs(nc_dir, exist_ok=True)
if plots:
    plot_dir_maps = os.path.join(metrics_output_path, "plots", "maps")
    os.makedirs(plot_dir_maps, exist_ok=True)

# Setting up model realization list
find_all_realizations, realizations = utilities.set_up_realizations(realization)

#### Do Obs part

f_nt_n = "/home/ordonez4/seaice/data/icecon_ssmi_nt_n.nc"
f_nt_s = "/home/ordonez4/seaice/data/icecon_ssmi_nt_s.nc"
f_bt_n = "/home/ordonez4/seaice/data/icecon_ssmi_bt_n.nc"
f_bt_s = "/home/ordonez4/seaice/data/icecon_ssmi_bt_s.nc"

obs = xc.open_dataset(f_nt_n)
# Get regions
data_arctic = obs[var].where(obs.lat > 0)
data_antarctic = obs[var].where(obs.lat < 0)
data_ca1 = obs[var].where(((obs.lat > 80) & (obs.lat <= 87.2) & (obs.lon > -120) & (obs.lon <= 90)))
data_ca2 = obs[var].where(((obs.lat > 65) & (obs.lat < 87.2)) & ((obs.lon > 90) | (obs.lon <= -120)))
data_ca = data_ca1 + data_ca2
data_np = obs[var].where((obs.lat > 35) & (obs.lat <= 65) & ((obs.lon > 90) | (obs.lon <= -120)))
data_na = obs[var].data.where((obs.lat > 45) & (obs.lat <= 80) & (obs.lon > -120) & (obs.lon <= 90)) 
data_na = data_na - data_na.where((obs.lat > 45) & (obs.lat <= 50) & (obs.lon > 30) & (obs.lon <= 60))
data_sa = obs[var].where(
    (obs.lat > -90) & (obs.lat <= -55) & 
    (obs.lon > -60) & (obs.lon <= 20))
data_sp = obs[var].where(
    (obs.lat > -90) & (obs.lat <= -55) & 
    ((obs.lon > 90) | (obs.lon <= -60)))
data_io = obs[var].where(
    (obs.lat > -90) & (obs.lat <= -55) & 
    (obs.lon > 20) & (obs.lon <= 90))
# Get ice extent TODO - convert area units?
total_extent_arctic_obs = (data_arctic.where(data_arctic > 15) * area).sum(skipna=True)
total_extent_antarctic_obs = (data_antarctic.where(data_antarctic > 15) * area).sum(skipna=True)
total_extent_ca_obs = (data_ca.where(data_ca > 15) * obs.area).sum(("lon","lat"),skipna=True)
total_extent_np_obs = (data_np.where(data_np > 15) * obs.area).sum(("lon","lat"),skipna=True)
total_extent_na_obs = (data_na.where(data_na > 15) * obs.area).sum(("lon","lat"),skipna=True)
total_extent_sa_obs = (data_sa.where(data_sa > 15) * obs.area).sum(("lon","lat"),skipna=True)
total_extent_sp_obs = (data_sp.where(data_sp > 15) * obs.area).sum(("lon","lat"),skipna=True)
total_extent_io_obs = (data_io.where(data_io > 15) * obs.area).sum(("lon","lat"),skipna=True)

clim_arctic_obs = total_extent_arctic_obs.temporal.climatology(freq="month")
clim_antarctic_obs = total_area_antarctic_obs.temporal.climatology(freq="month")
clim_ca_obs = total_extent_ca_obs.temporal.climatology(freq="month")
clim_np_obs = total_extent_np_obs.temporal.climatology(freq="month")
clim_na_obs = total_extent_na_obs.temporal.climatology(freq="month")
clim_sa_obs = total_extent_sa_obs.temporal.climatology(freq="month")
clim_sp_obs = total_extent_sp_obs.temporal.climatology(freq="month")
clim_io_obs = total_extent_io_obs.temporal.climatology(freq="month")

# Get climatology
# get errors for climo and mean

#### Do model part
# Loop over models
for model in model_loop_list:
    if find_all_realizations:
        tags = {"%(model)": model, "%(model_version)": model, "%(realization)": "*"}
        test_data_full_path = os.path.join(test_data_path, filename_template)
        test_data_full_path = utilities.replace_multi(test_data_full_path, tags)
        ncfiles = glob.glob(test_data_full_path)
        realizations = []
        for ncfile in ncfiles:
            realizations.append(ncfile.split("/")[-1].split(".")[3])
        print("=================================")
        print("model, runs:", model, realizations)
        list_of_runs = realizations
    else:
        list_of_runs = realizations

    metrics_dict["RESULTS"][model] = {}

    mean_extents = None
    # Loop over realizations
    for run in list_of_runs:

        # Get areacello

        if run == reference_data_set:
            units_adjust = ObsUnitsAdjust
        else:
            units_adjust = ModUnitsAdjust

        metrics_dict["RESULTS"][model][run] = {}

        # Find model data, determine number of files, check if they exist
        tags = {
                "%(variable)": varname,
                "%(model)": model,
                "%(model_version)": model,
                "%(realization)": run,
        }
        test_data_full_path = os.path.join(test_data_path, filename_template)
        test_data_full_path = utilities.replace_multi(test_data_full_path, tags)
        area_path = utilities.replace_multi(area_template,tags)
        start_year = msyear
        end_year = meyear
        yrs = [str(start_year), str(end_year)]  # for output file names
        test_data_full_path = glob.glob(test_data_full_path)
        test_data_full_path.sort()
        if len(test_data_full_path) == 0:
            print("")
            print("-----------------------")
            print("Not found: model, run, variable:", model, run, varname)
            continue
        else:
            print("")
            print("-----------------------")
            print("model, run, variable:", model, run, varname)
            print("test_data (model in this case) full_path:")
            for t in test_data_full_path:
                print("  ", t)

        # Load and prep data
        ds = utilities.load_dataset(test_data_full_path)
        area = utilities.load_dataset(area_path) #TODO: only once per model

        if any(ds.lon < -180) | any(ds.lon > 360):
            print("Invalid longitude range")
            continue

        # Get time slice if year parameters exist
        if start_year is not None:
            ds = utilities.slice_dataset(ds, start_year, end_year)
        else:
            # Get labels for start/end years from dataset
            yrs = [str(int(ds.time.dt.year[0])), str(int(ds.time.dt.year[-1]))]
        
        # Compute climatologies at some point

        data_arctic = ds[var].where(ds.lat > 0)
        data_antarctic = ds[var].where(ds.lat < 0)
        data_ca1 = ds[var].where(((ds.lat > 80) & (ds.lat <= 87.2) & (ds.lon > -120) & (ds.lon <= 90)))
        data_ca2 = ds[var].where(((ds.lat > 65) & (ds.lat < 87.2)) & ((ds.lon > 90) | (ds.lon <= -120)))
        data_ca = data_ca1 + data_ca2
        data_np = ds[var].where((ds.lat > 35) & (ds.lat <= 65) & ((ds.lon > 90) | (ds.lon <= -120)))
        data_na = ds[var].data.where((ds.lat > 45) & (ds.lat <= 80) & (ds.lon > -120) & (ds.lon <= 90)) 
        data_na = data_na - data_na.where((ds.lat > 45) & (ds.lat <= 50) & (ds.lon > 30) & (ds.lon <= 60))
        data_sa = ds[var].where(
            (ds.lat > -90) & (ds.lat <= -55) & 
            (ds.lon > -60) & (ds.lon <= 20))
        data_sp = ds[var].where(
            (ds.lat > -90) & (ds.lat <= -55) & 
            ((ds.lon > 90) | (ds.lon <= -60)))
        data_io = ds[var].where(
            (ds.lat > -90) & (ds.lat <= -55) & 
            (ds.lon > 20) & (ds.lon <= 90))

        if mean_extents is None:
            total_extent_arctic = np.zeros((len(list_of_runs),len(ds.time)))
            total_extent_antarctic = np.zeros((len(list_of_runs),len(ds.time)))
            total_extent_ca = np.zeros((len(list_of_runs),len(ds.time)))
            total_extent_np = np.zeros((len(list_of_runs),len(ds.time)))
            total_extent_na = np.zeros((len(list_of_runs),len(ds.time)))
            total_extent_sa = np.zeros((len(list_of_runs),len(ds.time)))
            total_extent_sp = np.zeros((len(list_of_runs),len(ds.time)))
            total_extent_io = np.zeros((len(list_of_runs),len(ds.time)))

        total_extent_arctic[run_ind,:] = (data_arctic.where(data_arctic > 15) * area).sum(skipna=True)
        total_extent_antarctic[run_ind,:] = (data_antarctic.where(data_antarctic > 15) * area).sum(skipna=True)
        total_extent_ca[run_ind,:] = (data_ca.where(data_ca > 15) * area).sum(("lon","lat"),skipna=True)
        total_extent_np[run_ind,:] = (data_np.where(data_np > 15) * area).sum(("lon","lat"),skipna=True)
        total_extent_na[run_ind,:] = (data_na.where(data_na > 15) * area).sum(("lon","lat"),skipna=True)
        total_extent_sa[run_ind,:] = (data_sa.where(data_sa > 15) * area).sum(("lon","lat"),skipna=True)
        total_extent_sp[run_ind,:] = (data_sp.where(data_sp > 15) * area).sum(("lon","lat"),skipna=True)
        total_extent_io[run_ind,:] = (data_io.where(data_io > 15) * area).sum(("lon","lat"),skipna=True)

    # Get average total over all realizations for this model
    # Get annual cycle of model average tseries
    # Get error compared to obs
    total_extent_arctic = np.mean(total_extent_arctic,axis=0)
    total_extent_antarctic = np.mean(total_extent_antarctic,axis=0)
    total_extent_ca = np.mean(total_extent_ca,axis=0)
    total_extent_np = np.mean(total_extent_np,axis=0)
    total_extent_na = np.mean(total_extent_na,axis=0)
    total_extent_sa = np.mean(total_extent_sa,axis=0)
    total_extent_sp = np.mean(total_extent_sp,axis=0)
    total_extent_io = np.mean(total_extent_io,axis=0)

    total_extent_arctic = ds.copy(data=total_extent_arctic).temporal.climatology(freq="month")
    total_extent_antarctic = ds.copy(data=total_extent_antarctic).temporal.climatology(freq="month")
    total_extent_ca = ds.copy(data=total_extent_ca).temporal.climatology(freq="month")
    total_extent_np = ds.copy(data=total_extent_np).temporal.climatology(freq="month")
    total_extent_na = ds.copy(data=total_extent_na).temporal.climatology(freq="month")
    total_extent_sa = ds.copy(data=total_extent_sa).temporal.climatology(freq="month")
    total_extent_sp = ds.copy(data=total_extent_sp).temporal.climatology(freq="month")
    total_extent_io = ds.copy(data=total_extent_io).temporal.climatology(freq="month")

    # get RMS for model mean annual cycle

    metrics_tmp = metrics_dict.copy()
    metrics_tmp["DIMENSIONS"]["model"] = model
    metrics_tmp["DIMENSIONS"]["realization"] = list_of_runs
    metrics_tmp["RESULTS"] = {model: metrics_dict["RESULTS"][model]}
    metrics_path = "{0}_block_extremes_metrics.json".format(model)
    utilities.write_to_json(metrics_output_path, metrics_path, metrics_tmp)

    meta.update_metrics(
        model,
        os.path.join(metrics_output_path, metrics_path),
        model + " results",
        "Seasonal metrics for block extrema for single dataset",
    )

    # reset for next model
    mean_extents = None

# Output single file with all models
model_write_list = model_loop_list.copy()
if "Reference" in model_write_list:
    model_write_list.remove("Reference")
metrics_dict["DIMENSIONS"]["model"] = model_write_list
utilities.write_to_json(
    metrics_output_path, "block_extremes_metrics.json", metrics_dict
)
fname = os.path.join(metrics_output_path, "block_extremes_metrics.json")
meta.update_metrics(
    "All", fname, "All results", "Seasonal metrics for block extrema for all datasets"
)


# Update and write metadata file
try:
    with open(fname, "r") as f:
        tmp = json.load(f)
    meta.update_provenance("environment", tmp["provenance"])
except Exception:
    # Skip provenance if there's an issue
    print("Error: Could not get provenance from extremes json for output.json.")

meta.update_provenance("modeldata", test_data_path)
if reference_data_path is not None:
    meta.update_provenance("obsdata", reference_data_path)
meta.write()