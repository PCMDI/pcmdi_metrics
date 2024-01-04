Sea ice metrics driver

Example command:

python -u ice_driver.py -p parameter_file.py --case_id E3SM-1-0 --test_data_set 'E3SM-1-0' --test_data_path '/p/css03/esgf_publish/CMIP6/CMIP/UCSB/E3SM-1-0/historical/%(realization)/SImon/siconc/gr/*/' --filename_template 'siconc_SImon_E3SM-1-0_historical_%(realization)_gr_*-*.nc' --area_template '/p/user_pub/work/CMIP6/CMIP/E3SM-Project/E3SM-1-0/historical/r1i1p1f1/Ofx/areacello/gr/v20210127/areacello_Ofx_E3SM-1-0_historical_r1i1p1f1_gr.nc' --area_var areacello