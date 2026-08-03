#!/usr/bin/env python
"""Example test script for QBO-MJO metrics computation."""

from pcmdi_metrics.qbo.lib import process_qbo_mjo_metrics


def test_example_cesm2():
    """Test with CESM2 sample data."""
    params = {
        "model": "CESM2",
        "exp": "historical",
        "member": "r1i1p1f1",
        "input_file": "/home/lee1043/work/DATA/CMIP6/CESM2/historical/Amon/ua/ua_Amon_CESM2_historical_r1i1p1f1_gn_185001-201412.nc",
        "input_file2": "/home/lee1043/work/DATA/CMIP6/CESM2/historical/day/rlut/rlut_day_CESM2_historical_r1i1p1f1_gn_????0101-????1231.nc",
        "varname": "ua",
        "level": 50,  # hPa (=mb)
        "varname2": "rlut",
        # "start": "1981-01",
        "start": "1979-01",
        # "end": "1988-12",
        "end": "2005-12",
        "regrid": False,
        "regrid_tool": "xesmf",
        "target_grid": "2x2",
        "taper_to_mean": True,
        "output_dir": "./output_data",
        "debug": False,
    }
    output_metrics = process_qbo_mjo_metrics(params)
    print(output_metrics)
    return output_metrics


def test_example_era5():
    """Test with ERA5 data."""
    params = {
        "model": "ERA5",
        "exp": None,
        "member": None,
        "input_file": "/home/lee1043/work/DATA/ERA5/qbo_mjo_input/ERA5_u50_monthly_1979-2021_rewrite.nc",
        "input_file2": "/home/lee1043/work/DATA/ERA5/qbo_mjo_input/ERA5_olr_daily_40s40n_1979-2021_rewrite.nc",
        "varname": "u50",
        "level": None,  # hPa (=mb)
        "varname2": "olr",
        "start": "1979-01",
        "end": "2010-12",
        "regrid": True,
        "regrid_tool": "xesmf",
        "target_grid": "2x2",
        "taper_to_mean": True,
        "output_dir": "./output_data",
        "debug": False,
    }
    output_metrics = process_qbo_mjo_metrics(params)
    print(output_metrics)
    return output_metrics


if __name__ == "__main__":
    # Run ERA5 example by default
    # test_example_era5()

    # Run CESM2 example
    test_example_cesm2()
