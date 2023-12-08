#!/usr/bin/env python
from pcmdi_metrics.mean_climate.lib import pmp_parser


def create_sea_ice_parser():
    parser = pmp_parser.PMPMetricsParser()
    parser.add_argument(
        "--case_id",
        dest="case_id",
        help="Defines a subdirectory to the metrics output, so multiple"
        + "cases can be compared",
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
        "-r",
        "--reference_data_set",
        default=None,
        type=str,
        nargs="+",
        dest="reference_data_set",
        help="List of observations or models that are used as a "
        + "reference against the test_data_set",
        required=False,
    )

    parser.add_argument(
        "--reference_data_path",
        default=None,
        dest="reference_data_path",
        help="Path for the reference climitologies",
        required=False,
    )

    parser.add_argument(
        "-t",
        "--test_data_set",
        type=str,
        nargs="+",
        dest="test_data_set",
        help="List of observations or models to test "
        + "against the reference_data_set",
        required=False,
    )

    parser.add_argument(
        "--test_data_path",
        dest="test_data_path",
        help="Path for the test climitologies",
        required=False,
    )

    parser.add_argument(
        "--realization",
        dest="realization",
        help="A simulation parameter",
        required=False,
    )

    parser.add_argument(
        "--filename_template",
        dest="filename_template",
        help="Template for climatology files",
        required=False,
    )

    parser.add_argument(
        "--metrics_output_path",
        dest="metrics_output_path",
        default=None,
        help="Directory of where to put the results",
        required=False,
    )

    parser.add_argument(
        "--filename_output_template",
        dest="filename_output_template",
        help="Filename for the interpolated test climatologies",
        required=False,
    )

    parser.add_argument(
        "--grid_area",
        des="areacell",
        help="Filename template for grid area",
        required=True
    )

    parser.add_argument(
        "--output_json_template",
        help="Filename template for results json files",
        required=False,
    )

    parser.add_argument(
        "--debug",
        dest="debug",
        action="store_true",
        help="Turn on debugging mode by printing more information to track progress",
        required=False,
    )
    parser.add_argument(
        "--plots",
        action="store_true",
        help="Set to True to generate figures.",
        required=False,
    )
    parser.add_argument(
        "--osyear", dest="osyear", type=int, help="Start year for reference data set"
    )
    parser.add_argument(
        "--msyear", dest="msyear", type=int, help="Start year for model data set"
    )
    parser.add_argument(
        "--oeyear", dest="oeyear", type=int, help="End year for reference data set"
    )
    parser.add_argument(
        "--meyear", dest="meyear", type=int, help="End year for model data set"
    )
    parser.add_argument(
        "--ObsUnitsAdjust",
        type=tuple,
        default=(False, 0, 0, None),
        help="For unit adjust for OBS dataset. For example:\n"
        "- (True, 'divide', 100.0, 'hPa')  # Pa to hPa\n"
        "- (True, 'subtract', 273.15, 'C')  # degK to degC\n"
        "- (False, 0, 0, None) # No adjustment (default)",
    )
    parser.add_argument(
        "--ModUnitsAdjust",
        type=tuple,
        default=(False, 0, 0, None),
        help="For unit adjust for model dataset. For example:\n"
        "- (True, 'divide', 100.0, 'hPa')  # Pa to hPa\n"
        "- (True, 'subtract', 273.15, 'C')  # degK to degC\n"
        "- (False, 0, 0, None) # No adjustment (default)",
    )

    return parser
