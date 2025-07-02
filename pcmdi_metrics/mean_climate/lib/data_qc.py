from pcmdi_metrics.stats import cor_xy


def data_qc(test_data_name, ds_test, ds_ref, var, varname):
    """
    Perform data quality control checks and adjustments on the test dataset.
    This function checks for common issues such as sign conventions in wind stress data.

    Parameters
    ----------
    test_data_name : str
        Name of the test dataset.
    ds_test : xarray.Dataset
        Test dataset to be checked and potentially modified.
    ds_ref : xarray.Dataset
        Reference dataset for comparison.
    var : str
        Variable name (e.g., 'tauu' or 'tauv') to be checked.
    varname : str
        Actual variable name in the dataset.

    Returns
    -------
    ds_test : xarray.Dataset
        The potentially modified test dataset after quality control checks.

    Notes
    -----
    This function currently checks for sign conventions in wind stress data ('tauu' and 'tauv').
    If the pattern correlation between the test and reference datasets is negative, it suggests
    an opposite sign convention, and the function will swap the sign of the test dataset variable.
    In addition, for 'tauu', it checks the tropical mean to further confirm sign consistency.
    """
    if var in ["tauu", "tauv"]:
        # Get time mean
        test_time_mean = ds_test[varname].mean(dim="time")
        ref_time_mean = ds_ref[varname].mean(dim="time")

        swap_sign = False

        # Check pattern correlation
        pattern_corr = cor_xy(test_time_mean, ref_time_mean)
        if pattern_corr < 0:
            print(
                f"{test_data_name}: likely opposite sign convention, diagnosed via pattern correlation"
            )
            swap_sign = True

        if var == "tauu":
            # Check tropical mean
            tropical_mean = test_time_mean.sel(lat=slice(-10, 10)).mean()
            # Pseudocode for checking sign consistency
            if tropical_mean > 0:
                print(
                    f"{test_data_name}: likely opposite sign convention, diagnosed via tropical mean"
                )
                swap_sign = True

        if swap_sign:
            print(f"{test_data_name}: swapping sign of {varname}")
            ds_test[varname] = -ds_test[varname]

    return ds_test
