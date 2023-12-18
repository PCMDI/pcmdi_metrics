import xarray as xr
import xcdat as xc
import numpy as np
import matplotlib.pyplot as plt
import glob
import json
import os


from pcmdi_metrics.mean_climate.lib import compute_statistics

def mse_t(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Temporal Mean Square Error",
            "Abstract": "Compute Temporal Mean Square Error",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    ds = dm.copy(deep=True)
    ds["diff_square"] = np.sum((dm[var] - do[var]) ** 2) / len(dm["time"])
    stat = ds["diff_square"].data
    return stat

def mse_model(dm, do, var=None):
    """Computes rms"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Square Error",
            "Abstract": "Compute Mean Square Error",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    ds = dm.copy(deep=True)
    if var is not None:
        ds["diff_square"] = ((dm[var] - do[var]) ** 2)
    else:
        ds["diff_square"] = ((dm - do) ** 2)
    stat = ds["diff_square"].data
    return stat

def to_ice_con_ds(da,obs):
    ds = xr.Dataset(data_vars={"ice_con": da,
                               "time_bnds": obs.time_bnds},
                 coords = {"time": obs.time})
    return ds

parser = create_sea_ice_parser.create_sea_ice_parser()
parameter = parser.get_parameter(argparse_vals_only=False)

# Parameters
# I/O settings
case_id = parameter.case_id
model_list = parameter.test_data_set
realization = parameter.realization
varname = parameter.vars
filename_template = parameter.filename_template
test_data_path = parameter.test_data_path
reference_data_path = parameter.reference_data_path
reference_data_set = parameter.reference_data_set
reference_sftlf_template = parameter.reference_sftlf_template
metrics_output_path = parameter.metrics_output_path
area_template = parameter.grid_area
area_var = parameter.area_var
ModUnitsAdjust = parameter.ModUnitsAdjust
ObsUnitsAdjust = parameter.ObsUnitsAdjust
#plots = parameter.plots
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

arctic_clims = {}
arctic_means = {}
arctic_files = {"nt": f_nt_n, "bt": f_bt_n}
for source in arctic_files:
    obs = xc.open_dataset(arctic_files[source])
    obs["ice_con"] = obs["ice_con"] * 0.01
    obs["area"] = obs["area"] * 1e-6
    # Get regions
    data_arctic = obs[var].where(obs.lat > 0)
    data_ca1 = obs[var].where(((obs.lat > 80) & (obs.lat <= 87.2) & (obs.lon > -120) & (obs.lon <= 90)))
    data_ca2 = obs[var].where(((obs.lat > 65) & (obs.lat < 87.2)) & ((obs.lon > 90) | (obs.lon <= -120)))
    data_ca = obs[var].where((data_ca1 > 0) | (data_ca2 > 0))
    data_np = obs[var].where((obs.lat > 35) & (obs.lat <= 65) & ((obs.lon > 90) | (obs.lon <= -120)))
    data_na = obs[var].where((obs.lat > 45) & (obs.lat <= 80) & (obs.lon > -120) & (obs.lon <= 90))

    # Get ice extent TODO - convert area units?
    total_extent_arctic_obs = (data_arctic.where(data_arctic > 15) * obs.area).sum(("x","y"),skipna=True)
    total_extent_ca_obs = (data_ca.where(data_ca > 0.15) * obs.area).sum(("x","y"),skipna=True)
    total_extent_np_obs = (data_np.where(data_np > 0.15) * obs.area).sum(("x","y"),skipna=True)
    total_extent_na_obs = (data_na.where(data_na > 0.15) * obs.area).sum(("x","y"),skipna=True)

    clim_arctic_obs = to_ice_con_ds(total_extent_arctic_obs,obs).temporal.climatology(var,freq="month")
    clim_ca_obs = to_ice_con_ds(total_extent_ca_obs,obs).temporal.climatology(var,freq="month")
    clim_np_obs = to_ice_con_ds(total_extent_np_obs,obs).temporal.climatology(var,freq="month")
    clim_na_obs = to_ice_con_ds(total_extent_na_obs,obs).temporal.climatology(var,freq="month")

    arctic_clims[source] = {
        "arctic": clim_arctic_obs,
        "ca": clim_ca_obs,
        "np": clim_np_obs,
        "na": clim_na_obs
    }

    arctic_means[source] = {
        "arctic": total_extent_arctic_obs.mean("time"),
        "ca": total_extent_ca_obs.mean("time"),
        "np": total_extent_np_obs.mean("time"),
        "na": total_extent_na_obs.mean("time")  
    }
    obs.close()

antarctic_clims = {}
antarctic_means = {}
antarctic_files = {"nt": f_nt_s, "bt": f_bt_s}
for source in antarctic_files:
    obs = xc.open_dataset(antarctic_files[source])
    obs["ice_con"] = obs["ice_con"] * 0.01
    obs["area"] = obs["area"] * 1e-6
    data_antarctic = obs[var].where(obs.lat < 0)
    data_sa = obs[var].where(
        (obs.lat > -90) & (obs.lat <= -55) & 
        (obs.lon > -60) & (obs.lon <= 20))
    data_sp = obs[var].where(
        (obs.lat > -90) & (obs.lat <= -55) & 
        ((obs.lon > 90) | (obs.lon <= -60)))
    data_io = obs[var].where(
        (obs.lat > -90) & (obs.lat <= -55) & 
        (obs.lon > 20) & (obs.lon <= 90))

    total_extent_antarctic_obs = (data_antarctic.where(data_antarctic > 15) * obs.area).sum(("x","y"),skipna=True)
    total_extent_sa_obs = (data_sa.where(data_sa > 0.15) * obs.area).sum(("x","y"),skipna=True)
    total_extent_sp_obs = (data_sp.where(data_sp > 0.15) * obs.area).sum(("x","y"),skipna=True)
    total_extent_io_obs = (data_io.where(data_io > 0.15) * obs.area).sum(("x","y"),skipna=True)

    clim_antarctic_obs = to_ice_con_ds(total_extent_antarctic_obs,obs).temporal.climatology(var,freq="month")
    clim_sa_obs = to_ice_con_ds(total_extent_sa_obs,obs).temporal.climatology(var,freq="month")
    clim_sp_obs = to_ice_con_ds(total_extent_sp_obs,obs).temporal.climatology(var,freq="month")
    clim_io_obs = to_ice_con_ds(total_extent_io_obs,obs).temporal.climatology(var,freq="month")

    antarctic_clims[source] = {
        "antarctic": clim_antarctic_obs,
        "io": clim_io_obs,
        "sp": clim_sp_obs,
        "sa": clim_sa_obs
    }

    antarctic_means[source] = {
        "antarctic": total_extent_antarctic_obs.mean("time"),
        "io": total_extent_io_obs.mean("time"),
        "sp": total_extent_sp_obs.mean("time"),
        "sa": total_extent_sa_obs.mean("time")  
    }
    obs.close()

# Get climatology
# get errors for climo and mean

#### Do model part
# Loop over models

for model in model_loop_list:
    if find_all_realizations:
        tags = {"%(model)": model, "%(model_version)": model, "%(realization)": "*"}
        test_data_full_path = os.path.join(test_data_path, filename_template)
        test_data_full_path = replace_multi(test_data_full_path, tags)
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
    for run_ind,run in enumerate(list_of_runs):

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
        test_data_full_path = replace_multi(test_data_full_path, tags)
        area_path = replace_multi(area_template,tags)
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
        ds = load_dataset(test_data_full_path)
        area = load_dataset(area_path) #TODO: only once per model
        area[areaname] = area[areaname] * area_units_adjust
        
        xvar = get_longitude(ds).name
        yvar = get_latitude(ds).name

        if (ds.lon < -180).any() | (ds.lon > 360).any():
            print("Invalid longitude range")
            continue
        if ds.lon.min() > -1:
            ds["lon"] = ds.lon - 180

        # Get time slice if year parameters exist
        if start_year is not None:
            ds = slice_dataset(ds, start_year, end_year)
        else:
            # Get labels for start/end years from dataset
            yrs = [str(int(ds.time.dt.year[0])), str(int(ds.time.dt.year[-1]))]
        
        # Compute climatologies at some point

        data_arctic = ds[var].where(ds.lat > 0)
        data_antarctic = ds[var].where(ds.lat < 0)
        data_ca1 = ds[var].where(((ds.lat > 80) & (ds.lat <= 87.2) & (ds.lon > -120) & (ds.lon <= 90)),0)
        data_ca2 = ds[var].where(((ds.lat > 65) & (ds.lat < 87.2)) & ((ds.lon > 90) | (ds.lon <= -120)),0)
        data_ca = data_ca1 + data_ca2
        data_np = ds[var].where((ds.lat > 35) & (ds.lat <= 65) & ((ds.lon > 90) | (ds.lon <= -120)),0)
        data_na = ds[var].where((ds.lat > 45) & (ds.lat <= 80) & (ds.lon > -120) & (ds.lon <= 90),0) 
        data_na = data_na - data_na.where((ds.lat > 45) & (ds.lat <= 50) & (ds.lon > 30) & (ds.lon <= 60),0)
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
            total_extent_arctic = (data_arctic.where(data_arctic > 15)/100 * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_antarctic = (data_antarctic.where(data_antarctic > 15)/100 * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_ca = (data_ca.where(data_ca > 15)/100 * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_np = (data_np.where(data_np > 15)/100 * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_na = (data_na.where(data_na > 15)/100 * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_sa = (data_sa.where(data_sa > 15)/100 * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_sp = (data_sp.where(data_sp > 15)/100 * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_io = (data_io.where(data_io > 15)/100 * area[areaname]).sum((xvar,yvar),skipna=True)
        else:
            total_extent_arctic = total_extent_arctic + (data_arctic.where(data_arctic > 15) * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_antarctic = total_extent_antarctic + (data_antarctic.where(data_antarctic > 15) * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_ca = total_extent_ca + (data_ca.where(data_ca > 15) * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_np = total_extent_np + (data_np.where(data_np > 15) * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_na = total_extent_na + (data_na.where(data_na > 15) * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_sa = total_extent_sa + (data_sa.where(data_sa > 15) * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_sp = total_extent_sp + (data_sp.where(data_sp > 15) * area[areaname]).sum((xvar,yvar),skipna=True)
            total_extent_io = total_extent_io + (data_io.where(data_io > 15) * area[areaname]).sum((xvar,yvar),skipna=True)

    # Get average total over all realizations for this model
    # Get annual cycle of model average tseries
    # Get error compared to obs

    # TODO: compute only for dask arrays
    total_extent_arctic = (total_extent_arctic / len(list_of_runs)).compute().to_dataset(name=varname)
    total_extent_antarctic = (total_extent_antarctic / len(list_of_runs)).compute().to_dataset(name=varname)
    total_extent_ca = (total_extent_ca / len(list_of_runs)).compute().to_dataset(name=varname)
    total_extent_np = (total_extent_np / len(list_of_runs)).compute().to_dataset(name=varname)
    total_extent_na = (total_extent_na / len(list_of_runs)).compute().to_dataset(name=varname)
    total_extent_sa = (total_extent_sa / len(list_of_runs)).compute().to_dataset(name=varname)
    total_extent_sp = (total_extent_sp / len(list_of_runs)).compute().to_dataset(name=varname)
    total_extent_io = (total_extent_io / len(list_of_runs)).compute().to_dataset(name=varname)
    
    total_extent_arctic.time.attrs.pop("bounds")
    total_extent_antarctic.time.attrs.pop("bounds")
    total_extent_ca.time.attrs.pop("bounds")
    total_extent_np.time.attrs.pop("bounds")
    total_extent_na.time.attrs.pop("bounds")
    total_extent_sa.time.attrs.pop("bounds")
    total_extent_sp.time.attrs.pop("bounds")
    total_extent_io.time.attrs.pop("bounds")
    
    total_extent_arctic = total_extent_arctic.bounds.add_missing_bounds()
    total_extent_antarctic = total_extent_antarctic.bounds.add_missing_bounds()
    total_extent_ca = total_extent_ca.bounds.add_missing_bounds()
    total_extent_np = total_extent_np.bounds.add_missing_bounds()
    total_extent_na = total_extent_na.bounds.add_missing_bounds()
    total_extent_sa = total_extent_sa.bounds.add_missing_bounds()
    total_extent_sp = total_extent_sp.bounds.add_missing_bounds()
    total_extent_io = total_extent_io.bounds.add_missing_bounds()

    clim_extent_arctic = total_extent_arctic.temporal.climatology("ice_con",freq=varname)
    clim_extent_antarctic = total_extent_antarctic.temporal.climatology("ice_con",freq=varname)
    clim_extent_ca = total_extent_ca.temporal.climatology(varname,freq="month")
    clim_extent_np = total_extent_np.temporal.climatology(varname,freq="month")
    clim_extent_na = total_extent_na.temporal.climatology(varname,freq="month")
    clim_extent_sa = total_extent_sa.temporal.climatology(varname,freq="month")
    clim_extent_sp = total_extent_sp.temporal.climatology(varname,freq="month")
    clim_extent_io = total_extent_io.temporal.climatology(varname,freq="month")

    

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