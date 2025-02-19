# Parallel run scripts

These scripts were used to generate sea ice results for CMIP models at LLNL. These scripts contain hard-coded paths and will require adjustment or rewriting before they can be used on other systems such as NERSC. The CMIP5 and CMIP6 scripts (sea_ice_parallel_cmip5*.py and sea_ice_parallel_cmip6*py) rely on xsearch to find model files. These scripts use the PMP parallel_submitter function to parallelize job submission. Users should investigate whether this is compatible with their computing platform before use.

Users may use these scripts as a reference for setting up their own CMIP job scripts.
