import xarray as xr
import xcdat as xc
import numpy as np
import matplotlib.pyplot as plt
import glob
import json
import os
import datetime
import cftime
import dask

from sea_ice_parser import create_sea_ice_parser
from pcmdi_metrics.mean_climate.lib import compute_statistics
from pcmdi_metrics.io import xcdat_openxml
from pcmdi_metrics.io.base import Base

class MetadataFile:
    # This class organizes the contents for the CMEC
    # metadata file called output.json, which describes
    # the other files in the output bundle.

    def __init__(self, metrics_output_path):
        self.outfile = os.path.join(metrics_output_path, "output.json")
        self.json = {
            "provenance": {
                "environment": "",
                "modeldata": "",
                "obsdata": "",
                "log": "",
            },
            "metrics": {},
            "data": {},
            "plots": {},
        }

    def update_metrics(self, kw, filename, longname, desc):
        tmp = {"filename": filename, "longname": longname, "description": desc}
        self.json["metrics"].update({kw: tmp})
        return

    def update_data(self, kw, filename, longname, desc):
        tmp = {"filename": filename, "longname": longname, "description": desc}
        self.json["data"].update({kw: tmp})
        return

    def update_plots(self, kw, filename, longname, desc):
        tmp = {"filename": filename, "longname": longname, "description": desc}
        self.json["plots"].update({kw: tmp})

    def update_provenance(self, kw, data):
        self.json["provenance"].update({kw: data})
        return

    def update_index(self, val):
        self.json["index"] = val
        return

    def write(self):
        with open(self.outfile, "w") as f:
            json.dump(self.json, f, indent=4)

def mse_t(dm, do, weights=None):
    """Computes mse"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Temporal Mean Square Error",
            "Abstract": "Compute Temporal Mean Square Error",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    if weights is None:
        stat = np.sum(((dm.data - do.data) ** 2)) / len(dm, axis=0)
    else:
        stat = np.sum(((dm.data - do.data) ** 2) * weights, axis=0)
    if isinstance(stat,dask.array.core.Array):
        stat = stat.compute()
    return stat

def mse_model(dm, do, var=None):
    """Computes mse"""
    if dm is None and do is None:  # just want the doc
        return {
            "Name": "Mean Square Error",
            "Abstract": "Compute Mean Square Error",
            "Contact": "pcmdi-metrics@llnl.gov",
        }
    if var is not None: # dataset
        stat = ((dm[var].data - do[var].data) ** 2)
    else: # dataarray
        stat = ((dm - do) ** 2)
    if isinstance(stat,dask.array.core.Array):
        stat = stat.compute()
    return stat


def get_longitude(ds: xr.Dataset) -> xr.DataArray:
    key_lon = xc.axis.get_dim_keys(ds, axis="X")
    lon = ds[key_lon]
    return(lon)


def get_latitude(ds: xr.Dataset) -> xr.DataArray:
    key_lat = xc.axis.get_dim_keys(ds, axis="Y")
    lat = ds[key_lat]
    return(lat)

def to_ice_con_ds(da,obs):
    ds = xr.Dataset(data_vars={"ice_con": da,
                               "time_bnds": obs.time_bnds},
                 coords = {"time": obs.time})
    return ds

def adjust_units(ds,adjust_tuple):
    action_dict = {
            "multiply": "*",
            "divide": "/",
            "add": "+",
            "subtract": "-"}
    if adjust_tuple[0]:
        print("Converting units by ",adjust_tuple[1],adjust_tuple[2])
        cmd = " ".join(["ds",str(action_dict[adjust_tuple[1]]),str(adjust_tuple[2])])
        ds = eval(cmd)
    return ds

def verify_output_path(metrics_output_path, case_id):
    if metrics_output_path is None:
        metrics_output_path = datetime.datetime.now().strftime("v%Y%m%d")
    if case_id is not None:
        metrics_output_path = metrics_output_path.replace("%(case_id)", case_id)
    if not os.path.exists(metrics_output_path):
        print("\nMetrics output path not found.")
        print("Creating metrics output directory", metrics_output_path)
        try:
            os.makedirs(metrics_output_path)
        except Exception as e:
            print("\nError: Could not create metrics output path", metrics_output_path)
            print(e)
            print("Exiting.")
            sys.exit()
    return metrics_output_path

def verify_years(start_year, end_year, msg="Error: Invalid start or end year"):
    if start_year is None and end_year is None:
        return
    elif start_year is None or end_year is None:
        # If only one of the two is set, exit.
        print(msg)
        print("Exiting")
        sys.exit()

def set_up_realizations(realization):
    find_all_realizations = False
    if realization is None:
        realization = ""
        realizations = [realization]
    elif isinstance(realization, str):
        if realization.lower() in ["all", "*"]:
            find_all_realizations = True
            realizations=[""]
        else:
            realizations = [realization]
    elif isinstance(realization, list):
        realizations = realization

    return find_all_realizations, realizations

def load_dataset(filepath):
    # Load an xarray dataset from the given filepath.
    # If list of netcdf files, opens mfdataset.
    # If list of xmls, open last file in list.
    if filepath[-1].endswith(".xml"):
        # Final item of sorted list would have most recent version date
        ds = xcdat_openxml.xcdat_openxml(filepath[-1])
    elif len(filepath) > 1:
        ds = xc.open_mfdataset(filepath, chunks=None)
    else:
        ds = xc.open_dataset(filepath[0])
    return ds

def replace_multi(string, rdict):
    # Replace multiple keyworks in a string template
    # based on key-value pairs in 'rdict'.
    for k in rdict.keys():
        string = string.replace(k, rdict[k])
    return string

if __name__ == "__main__":

    parser = create_sea_ice_parser()
    parameter = parser.get_parameter(argparse_vals_only=False)

    # Parameters
    # I/O settings
    case_id = parameter.case_id
    realization = parameter.realization
    var = parameter.var
    filename_template = parameter.filename_template
    test_data_path = parameter.test_data_path
    model_list = parameter.test_data_set
    reference_data_path = parameter.reference_data_path
    reference_data_set = parameter.reference_data_set
    metrics_output_path = parameter.metrics_output_path
    area_template = parameter.area_template
    area_var = parameter.area_var
    AreaUnitsAdjust = parameter.AreaUnitsAdjust
    ModUnitsAdjust = parameter.ModUnitsAdjust
    ObsUnitsAdjust = parameter.ObsUnitsAdjust
    #plots = parameter.plots
    msyear = parameter.msyear
    meyear = parameter.meyear
    osyear = parameter.osyear
    oeyear = parameter.oeyear

    print(model_list)
    model_list.sort()
    # Verifying output directory
    metrics_output_path = verify_output_path(metrics_output_path, case_id)

    if isinstance(reference_data_set, list):
        # Fix a command line issue
        reference_data_set = reference_data_set[0]

    # Verify years
    ok_mod = verify_years(
        msyear,
        meyear,
        msg="Error: Model msyear and meyear must both be set or both be None (unset).",
    )
    ok_obs = verify_years(
        osyear,
        oeyear,
        msg="Error: Obs osyear and oeyear must both be set or both be None (unset).",
    )

    # Initialize output.json file
    meta = MetadataFile(metrics_output_path)


    #if plots:
    #    plot_dir_maps = os.path.join(metrics_output_path, "plots", "maps")
    #    os.makedirs(plot_dir_maps, exist_ok=True)

    # Setting up model realization list
    find_all_realizations, realizations = set_up_realizations(realization)
    print("Find all realizations:",find_all_realizations)

    #### Do Obs part
    ObsUnitsAdjust=(True,"multiply",1e-2)
    ObsAreaUnitsAdjust=(False,0,0)

    f_nt_n = "/home/ordonez4/seaice/data/icecon_ssmi_nt_n_edited.nc"
    f_nt_s = "/home/ordonez4/seaice/data/icecon_ssmi_nt_s_edited.nc"
    f_bt_n = "/home/ordonez4/seaice/data/icecon_ssmi_bt_n_edited.nc"
    f_bt_s = "/home/ordonez4/seaice/data/icecon_ssmi_bt_s_edited.nc"

    arctic_clims = {}
    arctic_means = {}
    arctic_files = {"nt": f_nt_n, "bt": f_bt_n}
    obs_var="ice_con"

    print("OBS: Arctic")
    for source in arctic_files:
        obs = xc.open_dataset(arctic_files[source])
        obs[obs_var] = adjust_units(obs[obs_var],ObsUnitsAdjust)
        obs["area"] = adjust_units(obs["area"],ObsAreaUnitsAdjust)
        #mask=create_land_sea_mask(obs,lon_key="lon",lat_key="lat")
        # Get regions
        data_arctic = obs[obs_var].where((obs.lat > 0),0)
        data_ca1 = obs[obs_var].where(((obs.lat > 80) & (obs.lat <= 87.2) & (obs.lon > -120) & (obs.lon <= 90)),0)
        data_ca2 = obs[obs_var].where(((obs.lat > 65) & (obs.lat < 87.2)) & ((obs.lon > 90) | (obs.lon <= -120)),0)
        data_ca = obs[obs_var].where((data_ca1 > 0) | (data_ca2 > 0),0)
        data_np = obs[obs_var].where((obs.lat > 35) & (obs.lat <= 65) & ((obs.lon > 90) | (obs.lon <= -120)),0)
        data_na = obs[obs_var].where((obs.lat > 45) & (obs.lat <= 80) & (obs.lon > -120) & (obs.lon <= 90),0)
        data_na = data_na - data_na.where((obs.lat > 45) & (obs.lat <= 50) & (obs.lon > 30) & (obs.lon <= 60),0)

        # Get ice extent
        total_extent_arctic_obs = (data_arctic.where(data_arctic > 0.15) * obs.area).sum(("x","y"),skipna=True)
        total_extent_ca_obs = (data_ca.where(data_ca > 0.15) * obs.area).sum(("x","y"),skipna=True)
        total_extent_np_obs = (data_np.where(data_np > 0.15) * obs.area).sum(("x","y"),skipna=True)
        total_extent_na_obs = (data_na.where(data_na > 0.15) * obs.area).sum(("x","y"),skipna=True)

        clim_arctic_obs = to_ice_con_ds(total_extent_arctic_obs,obs).temporal.climatology(obs_var,freq="month")
        clim_ca_obs = to_ice_con_ds(total_extent_ca_obs,obs).temporal.climatology(obs_var,freq="month")
        clim_np_obs = to_ice_con_ds(total_extent_np_obs,obs).temporal.climatology(obs_var,freq="month")
        clim_na_obs = to_ice_con_ds(total_extent_na_obs,obs).temporal.climatology(obs_var,freq="month")

        arctic_clims[source] = {
            "arctic": clim_arctic_obs,
            "ca": clim_ca_obs,
            "np": clim_np_obs,
            "na": clim_na_obs
        }

        arctic_means[source] = {
            "arctic": total_extent_arctic_obs.mean("time",skipna=True).data.item(),
            "ca": total_extent_ca_obs.mean("time",skipna=True).data.item(),
            "np": total_extent_np_obs.mean("time",skipna=True).data.item(),
            "na": total_extent_na_obs.mean("time",skipna=True).data.item()  
        }
        obs.close()

    antarctic_clims = {}
    antarctic_means = {}
    antarctic_files = {"nt": f_nt_s, "bt": f_bt_s}
    print("OBS: Antarctic")
    for source in antarctic_files:
        obs = xc.open_dataset(antarctic_files[source])
        obs[obs_var] = adjust_units(obs[obs_var],ObsUnitsAdjust)
        obs["area"] = adjust_units(obs["area"],ObsAreaUnitsAdjust)
        data_antarctic = obs[obs_var].where((obs.lat < 0),0)
        data_sa = obs[obs_var].where(
            (obs.lat > -90) & (obs.lat <= -55) & 
            (obs.lon > -60) & (obs.lon <= 20),0)
        data_sp = obs[obs_var].where(
            (obs.lat > -90) & (obs.lat <= -55) & 
            ((obs.lon > 90) | (obs.lon <= -60)),0)
        data_io = obs[obs_var].where(
            (obs.lat > -90) & (obs.lat <= -55) & 
            (obs.lon > 20) & (obs.lon <= 90),0)

        total_extent_antarctic_obs = (data_antarctic.where(data_antarctic > 0.15) * obs.area).sum(("x","y"),skipna=True)
        total_extent_sa_obs = (data_sa.where(data_sa > 0.15) * obs.area).sum(("x","y"),skipna=True)
        total_extent_sp_obs = (data_sp.where(data_sp > 0.15) * obs.area).sum(("x","y"),skipna=True)
        total_extent_io_obs = (data_io.where(data_io > 0.15) * obs.area).sum(("x","y"),skipna=True)

        clim_antarctic_obs = to_ice_con_ds(total_extent_antarctic_obs,obs).temporal.climatology(obs_var,freq="month")
        clim_sa_obs = to_ice_con_ds(total_extent_sa_obs,obs).temporal.climatology(obs_var,freq="month")
        clim_sp_obs = to_ice_con_ds(total_extent_sp_obs,obs).temporal.climatology(obs_var,freq="month")
        clim_io_obs = to_ice_con_ds(total_extent_io_obs,obs).temporal.climatology(obs_var,freq="month")

        antarctic_clims[source] = {
            "antarctic": clim_antarctic_obs,
            "io": clim_io_obs,
            "sp": clim_sp_obs,
            "sa": clim_sa_obs
        }

        antarctic_means[source] = {
            "antarctic": total_extent_antarctic_obs.mean("time",skipna=True).data.item(),
            "io": total_extent_io_obs.mean("time",skipna=True).data.item(),
            "sp": total_extent_sp_obs.mean("time",skipna=True).data.item(),
            "sa": total_extent_sa_obs.mean("time",skipna=True).data.item()  
        }
        obs.close()
        
    obs_clims = {"nt": {},"bt":{}}
    obs_means = {"nt": {},"bt":{}}
    for item in antarctic_clims["nt"]:
        obs_clims["nt"][item] = antarctic_clims["nt"][item]
        obs_means["nt"][item] = antarctic_means["nt"][item]
        obs_clims["bt"][item] = antarctic_clims["bt"][item]
        obs_means["bt"][item] = antarctic_means["bt"][item]
    for item in arctic_clims["nt"]:
        obs_clims["nt"][item] = arctic_clims["nt"][item]
        obs_means["nt"][item] = arctic_means["nt"][item]
        obs_clims["bt"][item] = arctic_clims["bt"][item]
        obs_means["bt"][item] = arctic_means["bt"][item]

    # Get climatology
    # get errors for climo and mean

    #### Do model part
    # Loop over models

    clim_wts = [31., 28., 31., 30., 31., 30., 31., 31., 30., 31., 30., 31.]
    clim_wts = [x/365 for x in clim_wts]
    mse = {}
    metrics = {
        "DIMENSIONS": {
            "json_structure": [
                "model",
                "obs",
                "region",
                "index",
                "statistic",
            ],
            "region": {},
            "index": {
                "monthly_clim": "Monthly climatology of extent",
                "total_extent": "Sum of ice coverage where concentration > 15%"
                },
            "statistic": {
                "mse": "Mean Square Error (10^12 km^4)"
            },
            "model": model_list,
        },
        "RESULTS": {},
        "model_year_range": {}
    }

    for model in model_list:
        tags = {
                "%(variable)": var,
                "%(model)": model,
                "%(model_version)": model,
                "%(realization)": "*"
            }
        if find_all_realizations:
            test_data_full_path_tmp = os.path.join(test_data_path, filename_template)
            test_data_full_path_tmp = replace_multi(test_data_full_path_tmp, tags)
            ncfiles = glob.glob(test_data_full_path_tmp)
            print(ncfiles)
            realizations = []
            for ncfile in ncfiles:
                realizations.append(ncfile.split("/")[-1].split(".")[3])
            print("=================================")
            print("model, runs:", model, realizations)
            list_of_runs = realizations
        else:
            list_of_runs = realizations
        print(list_of_runs)

        start_year = msyear
        end_year = meyear

        totals_dict = {"arctic": 0,
                    "ca": 0,
                    "na": 0,
                    "np": 0,
                    "antarctic": 0,
                    "sp": 0,
                    "sa": 0,
                    "io": 0}
        mse[model] = {
            "nasateam": {},
            "bootstrap": {}
        }
        
        # Loop over realizations
        for run_ind,run in enumerate(list_of_runs):

            # Find model data, determine number of files, check if they exist
            tags = {
                    "%(variable)": var,
                    "%(model)": model,
                    "%(model_version)": model,
                    "%(realization)": run,
            }
            test_data_full_path = os.path.join(test_data_path, filename_template)
            test_data_full_path = replace_multi(test_data_full_path, tags)
            test_data_full_path = glob.glob(test_data_full_path)
            test_data_full_path.sort()
            if len(test_data_full_path) == 0:
                print("")
                print("-----------------------")
                print("Not found: model, run, variable:", model, run, var)
                continue
            else:
                print("")
                print("-----------------------")
                print("model, run, variable:", model, run, var)
                print("test_data (model in this case) full_path:")
                for t in test_data_full_path:
                    print("  ", t)

            # Model grid area
            print(area_template)
            print(replace_multi(area_template,tags))
            area = load_dataset(replace_multi(area_template,tags))
            area[area_var] = adjust_units(area[area_var],AreaUnitsAdjust)

            # Load and prep data
            ds = load_dataset(test_data_full_path)
            ds[var] = adjust_units(ds[var],ModUnitsAdjust)
            xvar = get_longitude(ds).name
            yvar = get_latitude(ds).name
            if (ds.lon < -180).any():
                ds["lon"] = ds.lon.where(ds.lon >= -180, ds.lon+360)
            if ds.lon.min() >= 0:
                ds["lon"] = ds.lon.where(ds.lon >= 180, ds.lon-360)

            # Get time slice if year parameters exist
            if start_year is not None:
                ds = ds.sel({"time":slice("{0}-01-01".format(start_year), "{0}-12-31".format(end_year))})
                yr_range = [str(start_year),str(end_year)]
            else:
                # Get labels for start/end years from dataset
                yr_range = [str(int(ds.time.dt.year[0])),str(int(ds.time.dt.year[-1]))]
            
            # Get regions
            data_arctic = ds[var].where(ds.lat > 0, 0)
            data_antarctic = ds[var].where(ds.lat < 0, 0)
            data_ca1 = ds[var].where((
                (ds.lat > 80) & 
                (ds.lat <= 87.2) & 
                (ds.lon > -120) & 
                (ds.lon <= 90)),0)
            data_ca2 = ds[var].where(
                ((ds.lat > 65) & (ds.lat < 87.2)) & 
                ((ds.lon > 90) | (ds.lon <= -120)),0)
            data_ca = data_ca1 + data_ca2
            data_np = ds[var].where(
                (ds.lat > 35) & 
                (ds.lat <= 65) & 
                ((ds.lon > 90) | (ds.lon <= -120)),0)
            data_na = ds[var].where(
                (ds.lat > 45) & 
                (ds.lat <= 80) & 
                (ds.lon > -120) & 
                (ds.lon <= 90),0) 
            data_na = data_na - data_na.where(
                (ds.lat > 45) & 
                (ds.lat <= 50) & 
                (ds.lon > 30) & 
                (ds.lon <= 60),0)
            data_sa = ds[var].where(
                (ds.lat > -90) & (ds.lat <= -55) & 
                (ds.lon > -60) & (ds.lon <= 20))
            data_sp = ds[var].where(
                (ds.lat > -90) & (ds.lat <= -55) & 
                ((ds.lon > 90) | (ds.lon <= -60)))
            data_io = ds[var].where(
                (ds.lat > -90) & (ds.lat <= -55) & 
                (ds.lon > 20) & (ds.lon <= 90))

            regions_dict = {
                "arctic": data_arctic,
                "antarctic": data_antarctic,
                "ca": data_ca,
                "np": data_np,
                "na": data_na,
                "sa": data_sa,
                "sp": data_sp,
                "io": data_io
            }

            # Running sum of all realizations
            for rgn in regions_dict:
                data = regions_dict[rgn]
                totals_dict[rgn] = totals_dict[rgn] + (data.where(data > 0.15, 0) * area[area_var]).sum((xvar,yvar),skipna=True)
            
            ds.close()
        
        for rgn in regions_dict:
            # Set up metrics dictionary
            for key in ["nasateam","bootstrap"]:
                mse[model][key][rgn] = {
                    "monthly_clim": {"mse": None},
                    "total_extent": {"mse": None}
                }
            
            # Average all realizations, fix bounds, get climatologies and totals
            total_rgn = (totals_dict[rgn] / len(list_of_runs)).to_dataset(name=var)
            #total_rgn.time.attrs.pop("bounds")
            total_rgn = total_rgn.bounds.add_missing_bounds()
            clim_extent = total_rgn.temporal.climatology(var,freq="month")
            total = total_rgn.mean("time")[var].data
            
            # Get errors, convert to 1e-12 km^-4
            mse[model]["nasateam"][rgn]["monthly_clim"]["mse"] = str(mse_t(clim_extent[var],obs_clims["nt"][rgn]["ice_con"],weights=clim_wts)*1e-12)
            mse[model]["bootstrap"][rgn]["monthly_clim"]["mse"] = str(mse_t(clim_extent[var],obs_clims["bt"][rgn]["ice_con"],weights=clim_wts)*1e-12)
            mse[model]["nasateam"][rgn]["total_extent"]["mse"] = str(mse_model(total,obs_means["nt"][rgn])*1e-12)
            mse[model]["bootstrap"][rgn]["total_extent"]["mse"] = str(mse_model(total,obs_means["bt"][rgn])*1e-12)
        
        # Update year list
        metrics["model_year_range"][model] = [str(start_year),str(end_year)]

    metrics["RESULTS"]=mse

    metricsfile = os.path.join(metrics_output_path,"metrics_demo.json")
    JSON = Base(metrics_output_path,"metrics_demo.json")
    json_structure = metrics["DIMENSIONS"]["json_structure"]
    JSON.write(
        metrics,
        json_structure=json_structure,
        sort_keys=True,
        indent=4,
        separators=(",", ": "),
    )
    meta.update_metrics("metrics", metricsfile, "metrics_JSON", "JSON file containig regional sea ice metrics")

    sector_list = ["Central Arctic Sector",
                "North Atlantic Sector",
                "North Pacific Sector",
                "Indian Ocean Sector",
                "South Atlantic Sector",
                "South Pacific Sector"]
    sector_short = ["ca","na","np","io","sa","sp"]
    fig7,ax7 = plt.subplots(6,1,figsize=(5,9))
    mlabels = model_list+["bootstrap"]
    ind = np.arange(len(mlabels))  # the x locations for the groups
    # ind = np.arange(len(mods)+1)  # the x locations for the groups
    width = 0.3
    n = len(ind) - 1
    for inds,sector in enumerate(sector_list):
        # Assemble data
        mse_clim = []
        mse_ext = []
        rgn = sector_short[inds]
        for model in model_list:
            mse_clim.append(float(metrics["RESULTS"][model]["nasateam"][rgn]["monthly_clim"]["mse"]))
            mse_ext.append(float(metrics["RESULTS"][model]["nasateam"][rgn]["total_extent"]["mse"]))
        mse_clim.append(mse_t(obs_clims["bt"][rgn]["ice_con"],obs_clims["nt"][rgn]["ice_con"],weights=clim_wts)*1e-12)
        mse_ext.append(mse_model(obs_means["bt"][rgn],obs_means["nt"][rgn])*1e-12)

        # Make figure
        ax7[inds].bar(ind, mse_clim, width, color="b")
        ax7[inds].bar(ind, mse_ext, width, color="r")
        #ax7[inds].bar(ind[n], obs[sector_short[inds]]**2, width, color="b")
        if inds==len(sector_list)-1:
            ax7[inds].set_xticks(ind + width / 2.0, mlabels, rotation=90, size=5)
        else:
            ax7[inds].set_xticks(ind + width/2.0,labels="")
        datamax=np.max(mse_clim)
        ymax = (datamax)*1.3
        ax7[inds].set_ylim(0.,ymax)
        if ymax < 1:
            ticks = np.linspace(0,1,5)
            labels = [str(round(x,1)) for x in ticks]
        elif ymax < 4:
            ticks = np.linspace(0,round(ymax),num=round(ymax/2)*4+1)
            labels = [str(round(x,1)) for x in ticks]
        elif ymax < 10:
            ticks = range(0,round(ymax))
            labels = [str(round(x,0)) for x in ticks]
        elif ymax > 10:
            ticks = range(0,round(ymax),2)
            labels = [str(round(x,0)) for x in ticks]
        ax7[inds].set_yticks(ticks,labels,fontsize=6)
        
        ax7[inds].set_ylabel("10${^12}$km${^4}$",size=6)
        ax7[inds].grid(True,linestyle=":")
        ax7[inds].annotate(
            sector,
            (0.35, 0.8),
            xycoords="axes fraction",
            size=8,
        )
    figfile=os.path.join(metrics_output_path,"demo_fig.png")
    plt.savefig(figfile)
    meta.update_plots("bar_chart", figfile, "regional_bar_chart", "Bar chart of regional MSE")

    # Update and write metadata file
    try:
        with open(os.path.join(metricsfile), "r") as f:
            tmp = json.load(f)
        meta.update_provenance("environment", tmp["provenance"])
    except Exception:
        # Skip provenance if there's an issue
        print("Error: Could not get provenance from metrics json for output.json.")

    meta.update_provenance("modeldata", test_data_path)
    if reference_data_path is not None:
        meta.update_provenance("obsdata", reference_data_path)
    meta.write()