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
        "--var",
        type=str,
        nargs="+",
        dest="var",
        help="Name of model sea ice concentration variable",
        required=False,
    )

    parser.add_argument(
        "--area_var",
        type=str,
        dest="area_var",
        help="Name of model area variable",
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
        "--area_template",
        dest="area_template",
        help="Filename template for model grid area",
        required=False
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
        default=(False, 0, 0),
        help="Factor to convert obs sea ice concentration to decimal. For example:\n"
        "- (True, 'divide', 100.0)  # percentage to decimal\n"
        "- (False, 0, 0) # No adjustment (default)",
    )
    parser.add_argument(
        "--ModUnitsAdjust",
        type=tuple,
        default=(False, 0, 0),
        help="Factor to convert model sea ice concentration to decimal. For example:\n"
        "- (True, 'divide', 100.0)  # percentage to decimal\n"
        "- (False, 0, 0) # No adjustment (default)",
    )
    parser.add_argument(
        "--AreaUnitsAdjust",
        type=tuple,
        default=(False, 0, 0),
        help="Factor to convert area data to km^2. For example:\n"
        "- (True, 'multiply', 1e-6)  # m^2 to km^2\n"
        "- (False, 0, 0) # No adjustment (default)",
    )

    parser.add_argument(
        "--ObsAreaUnitsAdjust",
        type=tuple,
        default=(False, 0, 0),
        help="Factor to convert area data to km^2. For example:\n"
        "- (True, 'multiply', 1e-6)  # m^2 to km^2\n"
        "- (False, 0, 0) # No adjustment (default)",
    )

    return parser
