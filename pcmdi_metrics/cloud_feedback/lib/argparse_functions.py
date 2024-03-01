import argparse

from cdp.cdp_parser import CDPParser


def AddParserArgument():
    P = CDPParser(
        default_args_file=[],
        description="Cloud feedback metrics",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    P.add_argument(
        "--model",
        type=str,
        dest="model",
        help="model name (e.g., GFDL-CM4).",
        required=False,
    )
    P.add_argument(
        "--institution",
        type=str,
        dest="institution",
        help="institution name (e.g., NOAA-GFDL).",
        default=None,
        required=False,
    )
    P.add_argument(
        "--variant",
        type=str,
        dest="variant",
        help="variant name (e.g., r1i1p1f1).",
        required=False,
    )
    P.add_argument(
        "--grid_label",
        type=str,
        dest="grid_label",
        help="grid_label (e.g., gr1).",
        default=None,
        required=False,
    )
    P.add_argument(
        "--version",
        type=str,
        dest="version",
        help="version (e.g., v20180701).",
        default=None,
        required=False,
    )
    P.add_argument(
        "--path",
        type=str,
        dest="path",
        help="path (e.g., /p/css03/esgf_publish/CMIP6).",
        required=False,
    )
    P.add_argument(
        "--input_files_json",
        type=str,
        dest="input_files_json",
        help="json file for list of input netCDF files (e.g., ./param/input_nc_files.json).",
        default=None,
        required=False,
    )
    P.add_argument(
        "--xml_path",
        type=str,
        dest="xml_path",
        help="path (e.g., ./xmls).",
        required=False,
    )
    P.add_argument(
        "--data_path",
        type=str,
        dest="data_path",
        help="path (e.g., ./data/).",
        default=None,
        required=False,
    )
    P.add_argument(
        "--figure_path",
        type=str,
        dest="figure_path",
        help="path (e.g., ./figures/).",
        default=None,
        required=False,
    )
    P.add_argument(
        "--output_path",
        type=str,
        dest="output_path",
        help="path (e.g., ./output/).",
        default="./output",
        required=False,
    )
    P.add_argument(
        "--output_json_filename",
        type=str,
        dest="output_json_filename",
        help="path (e.g., output.json).",
        default="output.json",
        required=False,
    )
    P.add_argument(
        "--get_ecs",
        type=bool,
        dest="get_ecs",
        help="Flag to compute ECS.\n"
        "True: compute ECS using abrupt-4xCO2 run.\n"
        "False: do not compute, instead rely on ECS value present in the json file (if it exists).",
        required=False,
    )
    P.add_argument(
        "--debug",
        type=bool,
        dest="debug",
        help="Flag to print interim results for debugging.\n"
        "True: print interim results and archive some of them.\n"
        "False: None (default).",
        default=None,
        required=False,
    )
    P.add_argument(
        "--cmec",
        dest="cmec",
        action="store_true",
        default=False,
        help="Save metrics in CMEC format",
    )
    P.add_argument(
        "--no_cmec",
        dest="cmec",
        action="store_false",
        default=False,
        help="Option to not save metrics in CMEC format",
    )

    param = P.get_parameter()

    return param
