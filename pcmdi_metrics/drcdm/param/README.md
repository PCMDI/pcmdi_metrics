# DRCDM Parameter files

## Basic parameter file

Users can look at drcdm_param.py as an example of a basic parameter file for the decision relevant climate data metrics. Take care to consult the documentation for these settings as user choices can change the metrics results. 

## Dataset specific files

The other directories under param/ contain parameter files and scripts to run the DRCDM driver for specific datasets on NERSC. These scripts are provided as-is with no warantee. These scripts will require edits before they can be run by a new user. Users should verify and change account numbers, conda environment names, and file paths as needed before attempting to run these scripts. They should also review the settings in the .py parameter files and update those as needed.

LOCA2/ and STAR-ESDM/ contain a script called "launch_all_for_model.py" which can be used to generate job scripts for a single model using the parameter file and batch job templates provided. For the observational datasets, users should manually edit and run the *.sh scripts provided. Many of these scripts contain informational comments and script code should be reviewed before running.
