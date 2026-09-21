
EXAMPLE Climatolgy Calculations with the PMP
--------------------------------------------

As with other PMP calculations input can be sent via a parameter file (using -p), via command line, or some combination of both with the command line entries overriding any common inputs in the parameter file.

Simple examples:

>  python ./clim_calc_driver.py -p clim_calc_cmip_inparam.py --start 1980-01 --end 2005-12

This computes the climatology for the model with the "infile" included in clim_calc_cmip_inparam.py

> python ./clim_calc_driver.py -p clim_calc_obs_inparam.py --outpath ./testout

This compute the climatology for the observational dataset included in clim_calc_obs_inparam.py.  With no start and end included, the climatology is computed for the entire time seres.

There are several options for defining the output directory and filename.
