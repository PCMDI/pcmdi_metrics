#!/usr/bin/env python
import glob
import hashlib
import json
import os
from copy import deepcopy

import geopandas as gpd
import numpy as np
import regionmask
import xcdat

from pcmdi_metrics.extremes.lib import (
    compute_metrics,
    create_extremes_parser,
    metadata,
    plot_extremes,
    region_utilities,
    return_value,
    utilities,
)


def latest_version_files(pattern):
    matches = glob.glob(pattern)
    if not matches:
        return []

    # The files are directly inside their vYYYYMMDD directory.
    version_dirs = {os.path.dirname(path) for path in matches}
    versions = {
        directory: int(os.path.basename(directory)[1:])
        for directory in version_dirs
        if os.path.basename(directory).startswith("v")
        and os.path.basename(directory)[1:].isdigit()
    }
    if len(versions) != len(version_dirs):
        raise ValueError(f"Expected vYYYYMMDD directories for {pattern}")

    newest = max(versions.values())
    newest_dirs = [
        directory for directory, version in versions.items() if version == newest
    ]
    if len(newest_dirs) != 1:
        raise ValueError(f"Multiple directories have version v{newest}: {newest_dirs}")

    chosen = newest_dirs[0]
    return sorted(path for path in matches if os.path.dirname(path) == chosen)


##########
# Set up
##########

parser = create_extremes_parser.create_extremes_parser()
parameter = parser.get_parameter(argparse_vals_only=False)

# Parameters
# I/O settings
case_id = parameter.case_id
model_list = parameter.test_data_set
realization = parameter.realization
variable_list = parameter.vars
filename_template = parameter.filename_template
sftlf_filename_template = parameter.sftlf_filename_template
test_data_path = parameter.test_data_path
reference_data_path = parameter.reference_data_path
reference_data_set = parameter.reference_data_set
reference_sftlf_template = parameter.reference_sftlf_template
metrics_output_path = parameter.metrics_output_path
ModUnitsAdjust = parameter.ModUnitsAdjust
ObsUnitsAdjust = parameter.ObsUnitsAdjust
# nc_out = parameter.nc_out
nc_out = True
plots = parameter.plots
debug = parameter.debug
cmec = parameter.cmec
msyear = parameter.msyear
meyear = parameter.meyear
osyear = parameter.osyear
oeyear = parameter.oeyear
generate_sftlf = parameter.generate_sftlf
regrid = parameter.regrid
cov_file = parameter.covariate_path
cov_name = parameter.covariate
return_period = parameter.return_period
norm = parameter.norm
# Block extrema related settings
annual_strict = parameter.annual_strict
exclude_leap = parameter.exclude_leap
dec_mode = parameter.dec_mode
drop_incomplete_djf = parameter.drop_incomplete_djf
# Region masking
shp_path = parameter.shp_path
col = parameter.attribute
region_name = parameter.region_name
coords = parameter.coords

# Multiple-region configuration. For shapefiles, use region_name="all" to
# analyze every distinct value in the `attribute` column, or supply comma-
# separated names. Single coordinate-defined regions remain supported.
regions = {}
if shp_path is not None:
    frame = gpd.read_file(shp_path)
    if col is None or col not in frame.columns:
        raise ValueError(f"Shapefile requires a valid attribute column: {col}")
    available = [str(v) for v in frame[col].dropna().unique()]
    if region_name is None or str(region_name).lower() == "all":
        requested = available
    elif isinstance(region_name, (list, tuple)):
        requested = [str(v) for v in region_name]
    else:
        requested = [v.strip() for v in str(region_name).split(",")]
    for name in requested:
        if name not in available:
            raise ValueError(
                f"Region {name!r} missing from {col}. Available: {available}"
            )
        if "_" in name:
            raise ValueError(f"Region {name!r} contains '_', unsupported in filenames")
        regions[name] = dict(shp_path=shp_path, column=col)
elif coords is not None:
    _, name, coords = region_utilities.check_region_params(
        None, coords, region_name, None, "land"
    )
    regions[name] = dict(coords=coords)
else:
    regions["land"] = {}

region_names = list(regions)
print("Regions:", region_names)


# Each shape is read once. Region masks are cached per *grid*, not per dataset.
# Use a 3D mask because named regions overlap (e.g., CONUS and NorthAmerica).
region_frame = None
regionmask_geometry = None
if shp_path is not None:
    region_frame = frame.dropna(subset=[col, "geometry"]).copy()
    region_frame[col] = region_frame[col].astype(str)
    region_frame = region_frame.dissolve(by=col, as_index=False)
    region_frame = region_frame.set_index(col).loc[region_names].reset_index()
    if region_frame.crs is not None and region_frame.crs.to_epsg() != 4326:
        region_frame = region_frame.to_crs(epsg=4326)
    regionmask_geometry = regionmask.from_geopandas(
        region_frame, names=col, overlap=True
    )

mask_cache = {}


def _grid_key(data):
    """Separate grids using coordinates, not only their shapes."""
    h = hashlib.sha256()
    for axis in ("lat", "lon"):
        values = np.ascontiguousarray(data[axis].values)
        h.update(str(values.shape).encode())
        h.update(str(values.dtype).encode())
        h.update(values.tobytes())
    return h.hexdigest()


def _all_grid_masks(data):
    key = _grid_key(data)
    if key not in mask_cache:
        if regionmask_geometry is not None:
            # drop=False retains regions with no grid cells on a coarse grid.
            masks = regionmask_geometry.mask_3D(data.lon, data.lat, drop=False)
            mask_cache[key] = {
                name: masks.isel(region=i, drop=True)
                for i, name in enumerate(region_names)
            }
        elif coords is not None:
            polygon = regionmask.Regions([np.asarray(coords, dtype=float)])
            m = polygon.mask_3D(data.lon, data.lat, drop=False)
            mask_cache[key] = {region_names[0]: m.isel(region=0, drop=True)}
        else:
            mask_cache[key] = {"land": None}
        print(f"Cached {len(mask_cache[key])} region masks for grid {key[:10]}")
    return mask_cache[key]


def mask_field(data, region):
    """Mask spatial fields, never cftime/time or lat/lon bounds."""
    mask = _all_grid_masks(data)[region]
    if mask is None:
        return data
    output = data.copy(deep=False)
    for var in data.data_vars:
        if "lat" in data[var].dims and "lon" in data[var].dims:
            output[var] = data[var].where(mask)
    return output


def mask_blocks(blocks, region):
    return {index: mask_field(block, region) for index, block in blocks.items()}


def materialize_extremes(ds):
    """Resolve mixed Dask/NumPy outputs before repeatedly writing/masking."""
    if any(hasattr(ds[var].data, "__dask_graph__") for var in ds.data_vars):
        print("Computing lazy block-extrema fields once")
        return ds.compute()
    return ds


def merge_region_results(destination, new_result):
    for index, regional in new_result.items():
        destination.setdefault(index, {}).update(regional)


def write_checked(ds, model, run, region, index, years, directory, description):
    """Use PMP writer, but fail immediately if a write silently fails."""
    global meta
    path = os.path.join(
        directory, f"{model}_{run}_{region}_{index}_{'-'.join(map(str, years))}.nc"
    )
    if os.path.exists(path):
        os.remove(path)  # prevents failed writes from reopening stale files
    meta = utilities.write_to_nc(
        ds, model, run, region, index, years, directory, description, meta
    )
    if not os.path.isfile(path):
        raise RuntimeError(f"Failed to write NetCDF: {path}")
    with xcdat.open_dataset(path) as checked:
        if "ANN" not in checked:
            raise RuntimeError(f"NetCDF missing ANN after write: {path}")
    return path


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
# Intermediate full-grid files remain separate from user-facing regional files.
full_nc_dir = os.path.join(metrics_output_path, "netcdf_full_grid")
os.makedirs(full_nc_dir, exist_ok=True)
full_block_files = {}  # (model, index) -> paths for all realizations
full_block_by_run = {}  # (model, run, index) -> path
if plots:
    plot_dir_maps = os.path.join(metrics_output_path, "plots", "maps")
    os.makedirs(plot_dir_maps, exist_ok=True)
    if reference_data_path is not None:
        plot_dir_taylor = os.path.join(metrics_output_path, "plots", "taylor")
        os.makedirs(plot_dir_taylor, exist_ok=True)

# Setting up model realization list
find_all_realizations, realizations = utilities.set_up_realizations(realization)

# Only include reference data in loop if it exists
if reference_data_path is not None:
    model_loop_list = ["Reference"] + model_list
else:
    model_loop_list = model_list

# Initialize output JSON structures
# FYI: if the analysis output JSON is changed, remember to update this function!
metrics_dict = compute_metrics.init_metrics_dict(
    model_loop_list,
    variable_list,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    region_names[0],
)
metrics_dict["DIMENSIONS"]["region"] = {
    name: "Land grid cells (sftlf >= 50) within region" for name in region_names
}

obs = {}

##############
# Run Analysis
##############

# Loop over models
for model in model_loop_list:
    if model == "Reference":
        list_of_runs = [str(reference_data_set)]
    elif find_all_realizations:
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

    # Loop over realizations
    for run in list_of_runs:
        # SFTLF
        sftlf_exists = True
        if run == reference_data_set:
            if reference_sftlf_template is not None and os.path.exists(
                reference_sftlf_template
            ):
                sftlf_filename = reference_sftlf_template
            else:
                print("No reference sftlf file template provided.")
                if not generate_sftlf:
                    print("Skipping reference data")
                else:
                    # Set flag to generate sftlf after loading data
                    sftlf_exists = False
        else:
            try:
                tags = {
                    "%(model)": model,
                    "%(model_version)": model,
                    "%(realization)": run,
                }
                sftlf_filename_list = utilities.replace_multi(
                    sftlf_filename_template, tags
                )
                sftlf_filename = glob.glob(sftlf_filename_list)[0]
            except (AttributeError, IndexError):
                print("No sftlf file found for", model, run)
                if not generate_sftlf:
                    print("Skipping realization", run)
                    continue
                else:
                    # Set flag to generate sftlf after loading data
                    sftlf_exists = False
        if sftlf_exists:
            sftlf = xcdat.open_dataset(sftlf_filename, decode_times=False)
            # Stats calculation is expecting sfltf scaled from 0-100
            if sftlf["sftlf"].max() <= 20:
                sftlf["sftlf"] = sftlf["sftlf"] * 100.0

        if run == reference_data_set:
            units_adjust = ObsUnitsAdjust
        else:
            units_adjust = ModUnitsAdjust

        metrics_dict["RESULTS"][model][run] = {}

        # Loop over variables - tasmax, tasmin, or pr
        for varname in variable_list:
            # Find model data, determine number of files, check if they exist
            if run == reference_data_set:
                test_data_full_path = reference_data_path
                start_year = osyear
                end_year = oeyear
            else:
                tags = {
                    "%(variable)": varname,
                    "%(model)": model,
                    "%(model_version)": model,
                    "%(realization)": run,
                }
                test_data_full_path = os.path.join(test_data_path, filename_template)
                test_data_full_path = utilities.replace_multi(test_data_full_path, tags)
                start_year = msyear
                end_year = meyear
            yrs = [str(start_year), str(end_year)]  # for output file names
            # test_data_full_path = glob.glob(test_data_full_path)
            # test_data_full_path.sort()
            print(test_data_full_path)

            if run == reference_data_set:
                test_data_full_path = sorted(glob.glob(test_data_full_path))
            else:
                test_grids = ["gn", "gr", "gr1", "gr2", "g110", "g150"]
                file_template = test_data_full_path

                for grid in test_grids:
                    test_data_full_path = latest_version_files(
                        file_template.replace("/gn/", f"/{grid}/").replace(
                            "_gn_", f"_{grid}_"
                        )
                    )

                    if len(test_data_full_path) > 0:
                        print(f"Using grid {grid}")
                        break

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

            if run == reference_data_set:
                rename = {
                    old: new
                    for old, new in {
                        "latitude": "lat",
                        "longitude": "lon",
                    }.items()
                    if old in ds.dims or old in ds.coords or old in ds.data_vars
                }
                ds = ds.rename(rename)

            if not sftlf_exists and generate_sftlf:
                print("Generating land sea mask.")
                sftlf = utilities.generate_land_sea_mask(ds, debug=debug)

            # Mask out Antarctica
            sftlf["sftlf"] = sftlf["sftlf"].where(sftlf.lat > -60)

            # Get time slice if year parameters exist
            if start_year is not None:
                ds = utilities.slice_dataset(ds, start_year, end_year)
            else:
                # Get labels for start/end years from dataset
                yrs = [str(int(ds.time.dt.year[0])), str(int(ds.time.dt.year[-1]))]

            if ds.time.encoding["calendar"] != "noleap" and exclude_leap:
                ds = ds.convert_calendar("noleap")

            # This dict is going to hold results for just this run
            stats_dict = {}

            # Generate all gridded temporal indices ONCE, then subset by region.
            if varname in ("tasmax", "tas"):
                TXx, TXn = compute_metrics.temperature_indices(
                    ds,
                    varname,
                    sftlf,
                    units_adjust,
                    dec_mode,
                    drop_incomplete_djf,
                    annual_strict,
                )
                stats_dict = {"TXx": TXx, "TXn": TXn}
            elif varname == "tasmin":
                TNx, TNn = compute_metrics.temperature_indices(
                    ds,
                    varname,
                    sftlf,
                    units_adjust,
                    dec_mode,
                    drop_incomplete_djf,
                    annual_strict,
                )
                stats_dict = {"TNx": TNx, "TNn": TNn}
            elif varname in ("pr", "PRECT", "precip"):
                if varname != "pr":
                    ds = ds.rename({varname: "pr"})
                Rx1day, Rx5day = compute_metrics.precipitation_indices(
                    ds,
                    sftlf,
                    units_adjust,
                    dec_mode,
                    drop_incomplete_djf,
                    annual_strict,
                )
                stats_dict = {"Rx1day": Rx1day, "Rx5day": Rx5day}
            else:
                continue

            # Time reductions can be lazy. Compute exactly once even when
            # subsequent regional NetCDF writes are eager.
            stats_dict = {
                index: materialize_extremes(block)
                for index, block in stats_dict.items()
            }

            # Store one unmasked (apart from the pre-existing sftlf land mask)
            # block file for each realization/index, for *one* GEV fit later.
            for index, block in stats_dict.items():
                full_path = write_checked(
                    block,
                    model,
                    run,
                    "fullGrid",
                    index,
                    yrs,
                    full_nc_dir,
                    f"Full-grid seasonal block extrema for {index}",
                )
                full_block_files.setdefault((model, index), []).append(full_path)
                full_block_by_run[(model, run, index)] = full_path

            for region in region_names:
                region_stats = mask_blocks(stats_dict, region)
                # Only retain the reference corresponding to this region.
                if model == "Reference":
                    obs.setdefault(region, {}).update(region_stats)

                for index, block in region_stats.items():
                    if nc_out:
                        description = f"Seasonal block extrema: {index} ({region})"
                        path = write_checked(
                            block,
                            model,
                            run,
                            region,
                            index,
                            yrs,
                            nc_dir,
                            description,
                        )
                        block = xcdat.open_dataset(path)
                        region_stats[index] = block
                        if model == "Reference":
                            obs[region][index] = block

                    if plots:
                        ref = (
                            obs.get(region, {}).get(index)
                            if model != "Reference"
                            else None
                        )
                        meta = plot_extremes.make_maps(
                            block,
                            model,
                            run,
                            region,
                            index,
                            [start_year, end_year],
                            plot_dir_maps,
                            f"Seasonal block extrema: {index}",
                            meta,
                            ref_data=ref,
                        )

                if model != "Reference":
                    print("Generating metrics for", region)
                    result = compute_metrics.metrics_json(
                        region_stats,
                        obs_dict=obs.get(region, {}),
                        region=region,
                        regrid=regrid,
                    )
                    merge_region_results(metrics_dict["RESULTS"][model][run], result)
                    if run not in metrics_dict["DIMENSIONS"]["realization"]:
                        metrics_dict["DIMENSIONS"]["realization"].append(run)

    if model != "Reference":
        # Pull out metrics for just this model
        # and write to JSON
        metrics_tmp = deepcopy(metrics_dict)
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

# Taylor Diagram
if plots and (reference_data_path is not None):
    print("Making Taylor Diagrams")
    years = "-".join(str(year) for year in yrs)
    outfile_template = os.path.join(
        plot_dir_taylor,
        "_".join(["taylor", "realization", "region", "index", "season", years]),
    )
    try:
        plot_extremes.taylor_diag(fname, outfile_template)
        meta.update_plots(
            "Taylor_Diagrams",
            outfile_template,
            "Taylor Diagrams",
            "Taylor Diagrams for block extrema results.",
        )
    except Exception as e:
        print("Error. Could not create Taylor Diagram for ", outfile_template, ":")
        print(e)

# Fit GEV exactly ONCE per model/index (across all its realizations).
# Input files are full-grid block extrema, never region-specific NetCDFs.
print("Generating full-grid return values (one fit per model/index).")
rv_full_files = {}  # (model, index) -> (rv output path, realization key)
for (model, stat), block_files in sorted(full_block_files.items()):
    if model == "Reference" and cov_file is not None:
        continue
    block_files = sorted(block_files)
    maxes = stat in ("TXx", "TNx", "Rx5day", "Rx1day")

    # compute_rv_for_model names output Model_fullGrid_STAT_YEARS_return_value.nc
    # compute_rv_from_file names Model_RUN_fullGrid_STAT_YEARS_return_value.nc
    if len(block_files) > 1:
        block_base = os.path.basename(block_files[0])
        model_prefix, rest = block_base.split("_", 1)
        # Remove only the realization; avoid fragile global str.replace().
        candidate = os.path.join(
            full_nc_dir,
            f"{model_prefix}_{rest.split('_', 1)[1].removesuffix('.nc')}_return_value.nc",
        )
        rv_run = "all"
    else:
        candidate = block_files[0].removesuffix(".nc") + "_return_value.nc"
        rv_run = os.path.basename(block_files[0]).split("_")[1]

    # A stale fit from an earlier execution must not be reused after an
    # input block file has been regenerated.
    needs_fit = not os.path.exists(candidate) or any(
        os.path.getmtime(p) > os.path.getmtime(candidate) for p in block_files
    )
    if needs_fit:
        if len(block_files) > 1:
            meta = return_value.compute_rv_for_model(
                block_files,
                cov_file,
                cov_name,
                full_nc_dir,
                return_period,
                meta,
                maxes=maxes,
                norm=norm,
            )
        else:
            meta = return_value.compute_rv_from_file(
                block_files,
                cov_file,
                cov_name,
                full_nc_dir,
                return_period,
                meta,
                maxes=maxes,
                norm=norm,
            )
    else:
        print("Reusing existing full-grid GEV fit:", candidate)

    if os.path.exists(candidate):
        rv_full_files[(model, stat)] = (candidate, rv_run)
    else:
        print("WARNING: no return-value file generated for", model, stat)

rv_metrics_dict = compute_metrics.init_metrics_dict(
    model_loop_list,
    variable_list,
    dec_mode,
    drop_incomplete_djf,
    annual_strict,
    region_names[0],
)
rv_metrics_dict["DIMENSIONS"]["region"] = dict(metrics_dict["DIMENSIONS"]["region"])

# Cache masked observations by region and index.
regional_reference_rvs = {}
regional_reference_blocks = {}
if cov_file is None:
    for (model, stat), (full_rv_path, rv_run) in sorted(
        rv_full_files.items(), key=lambda item: (item[0][0] != "Reference", item[0])
    ):
        print("Regionalizing return values:", model, stat)
        full_rv = xcdat.open_dataset(full_rv_path)
        # RVs for ensembles reference the first block realization, as before.
        first_block_file = sorted(full_block_files[(model, stat)])[0]
        full_bm = xcdat.open_dataset(first_block_file)
        full_se_path = full_rv_path.replace("_return_value.nc", "_standard_error.nc")
        full_se = (
            xcdat.open_dataset(full_se_path) if os.path.exists(full_se_path) else None
        )
        for region in region_names:
            rv = mask_field(full_rv, region)
            bm = mask_field(full_bm, region)
            # NetCDF bounds/coords remain intact.
            yrange = [
                str(osyear if model == "Reference" else msyear),
                str(oeyear if model == "Reference" else meyear),
            ]
            # Save regional gridded fitted RV and SE without refitting.
            # Preserve input full-grid base name, replacing only fullGrid.
            regional_rv_name = os.path.basename(full_rv_path).replace(
                "_fullGrid_", f"_{region}_", 1
            )
            regional_rv_path = os.path.join(nc_dir, regional_rv_name)
            utilities.write_netcdf_file(regional_rv_path, rv)
            meta.update_data(
                os.path.basename(regional_rv_path),
                regional_rv_path,
                "return_value",
                f"{return_period}-year regional return value",
            )
            if full_se is not None:
                regional_se = mask_field(full_se, region)
                regional_se_path = regional_rv_path.replace(
                    "_return_value.nc", "_standard_error.nc"
                )
                utilities.write_netcdf_file(regional_se_path, regional_se)
                meta.update_data(
                    os.path.basename(regional_se_path),
                    regional_se_path,
                    "standard_error",
                    "Regional GEV return value standard error",
                )

            if model == "Reference":
                regional_reference_rvs[(region, stat)] = rv
                regional_reference_blocks[(region, stat)] = bm
                continue

            refds = regional_reference_rvs.get((region, stat))
            bm_ref = regional_reference_blocks.get((region, stat))
            if plots:
                try:
                    meta = plot_extremes.make_maps(
                        rv,
                        model,
                        f"{rv_run}_return_value",
                        region,
                        stat,
                        yrange,
                        plot_dir_maps,
                        f"{return_period}-year return value for {stat}",
                        meta,
                        ref_data=refds,
                    )
                except Exception as exc:
                    print("Could not plot RV", model, region, stat, exc)

            tmp = compute_metrics.metrics_json_return_value(
                rv.copy(deep=True),
                bm,
                refds.copy(deep=True) if refds is not None else None,
                bm_ref,
                stat,
                region=region,
                regrid=regrid,
            )
            slot = (
                rv_metrics_dict["RESULTS"].setdefault(model, {}).setdefault(rv_run, {})
            )
            merge_region_results(slot, tmp)

        full_rv.close()
        full_bm.close()
        if full_se is not None:
            full_se.close()

    rv_metrics_dict["DIMENSIONS"]["model"] = [
        m for m in model_loop_list if m != "Reference"
    ]
    utilities.write_to_json(
        metrics_output_path, "return_value_metrics.json", rv_metrics_dict
    )
    rv_fname = os.path.join(metrics_output_path, "return_value_metrics.json")
    meta.update_metrics(
        "All",
        rv_fname,
        "All results",
        "Seasonal regional metrics for fitted return values",
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
