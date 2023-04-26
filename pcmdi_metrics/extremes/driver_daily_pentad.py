import xarray as xr
import pandas as pd
import numpy as np
import cftime
import datetime
from pcmdi_metrics.extremes.lib import (
    create_extremes_parser
)

# Parser
parser = create_extremes_parser()


parser.add_argument(
        "--test_data_path",
        dest="test_data_path",
        help="Path for the test climitologies",
        required=False,
    )
parser.add_argument(
        "-v",
        "--vars",
        type=str,
        nargs="+",
        dest="vars",
        help="Variables to use",
        required=False,
    )
parser.add_argument(
        "--filename_template",
        dest="filename_template",
        help="Template for climatology files",
        required=False,
    )
parser.add_argument(
        "--sftlf_filename_template",
        dest="sftlf_filename_template",
        help='Filename template for landsea masks ("sftlf")',
        required=False,
    )
parser.add_argument(
        "--metrics_output_path",
        dest="metrics_output_path",
        help="Directory of where to put the results",
        required=False,
    )
parser.add_argument(
    "--realization",
    type=str,
    dest="realization",
    default=None,
    help="realization"
)
parser.add_argument(
    "--chunk_size",
    type=int,
    dest="chunk_size",
    default=None,
    help="chunk size for latitude and longitude"
)
parser.add_argument(
        "--cmec",
        dest="cmec",
        action="store_true",
        help="Save metrics in CMEC format",
        required=False,
    )
parser.add_argument(
        "--no_cmec",
        dest="cmec",
        action="store_false",
        help="Option to not save metrics in CMEC format",
        required=False,
    )

args = parser.get_parameter()
model_list = args.modnames
modpath = args.modpath
pathout = args.results_dir
chunks = args.chunk_size

print("MODELPATH IS ", modpath)
print("PRINT P.view_args() = ", P.view_args())

print("Begin computing rolling means")

for model in model_list:
    print(model)
    
    # Chunks for potential dask https://docs.xarray.dev/en/stable/user-guide/dask.html
    model_pathout = os.path.join(pathout,var+"_max_pentad_"+mod_name+".nc")
    
    # For Single File
    if model_path:
        if chunk_size:
            f = xr.open_dataset(
                model_path,
                chunks={"lon": chunk_size, "lat": chunk_size})
        else:
            f = xr.open_dataset(model_path)
    elif model_dir_path:
        if chunk_size:
            f = xr.open_mfdataset(
                model_dir_path,
                chunks={"lon": chunk_size, "lat": chunk_size},
                parallel=True)
        else:
            f = xr.open_mfdataset(model_dir_path)
    
    # Analysis code here

    # Write outputs to netcdf file
    merged_dataset = xr.merge([
        ds_ann_max,
        ds_DJF_max,
        ds_MAM_max,
        ds_JJA_max,
        ds_SON_max])
    merged_dataset.to_netcdf(
        path=model_pathout,
        mode="w",
        format="NETCDF4")
