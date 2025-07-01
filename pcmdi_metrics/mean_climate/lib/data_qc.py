from pcmdi_metrics.stats import cor_xy


def data_qc(test_data_name, ds_test, ds_ref, var, varname):
    if var in ["tauu", "tauv"]:
        # Get time mean 
        test_time_mean = ds_test[varname].mean(dim="time")
        ref_time_mean = ds_ref[varname].mean(dim="time")
        
        swap_sign = False
        
        # Check pattern correlation
        pattern_corr = cor_xy(test_time_mean, ref_time_mean)
        if pattern_corr < 0:
            print(f"{test_data_name}: likely opposite sign convention, diagnosed via pattern correlation")
            swap_sign = True
        
        if var == "tauu":
            # Check tropical mean
            tropical_mean = test_time_mean.sel(lat=slice(-10, 10)).mean()
            # Pseudocode for checking sign consistency
            if tropical_mean > 0:
                print(f"{test_data_name}: likely opposite sign convention, diagnosed via tropical mean")
                swap_sign = True
            
        if swap_sign:
            print(f"{test_data_name}: swapping sign of {varname}")
            ds_test[varname] = -ds_test[varname]
            
    return ds_test
            
        