.. title:: PMP Support Data


***************
Retrieving data
***************

Demo data
~~~~~~~~~

Sample model and observational data are provided via a `jupyter notebook demo <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_0_download_data.ipynb>`_.  This is the first of multiple PMP demos. It enables a user to download all sample data before running the other demos that provide interactive examples of the different summary statistics provided by the PMP.  More info is available for `preparing to run these notebooks <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/README.md>`_.  

For users that are unfamiliar with Jupyter notebooks or just want to download the sample data without interactively running the demo, you can download the data by launching python from a PMP environment created from conda.  You can then enter the following form the python command prompt :: 

    import requests
    r = requests.get("https://pcmdiweb.llnl.gov/pss/pmpdata/pmp_tutorial_files.v20240201.txt")
    with open("data_files.txt", "wb") as f:
       f.write(r.content)

A location where you want to store the demo data locally can be set: ::

    demo_data_directory = 'MyDemoPath' 


After you have set the location for the demo_output you can download it by entering the following: ::

    from pcmdi_metrics.io.base import download_sample_data_files
    download_sample_data_files("data_files.txt", demo_data_directory)

The PMP demo data is used for multiple demos. It is ~300MB. The best way to run these demos is via Jupyter notebooks.  Running this initial demo for downloading sample data also on-the-fly creates demo parameter files with the user selection of the demo_data_directory. 

Reference datasets
~~~~~~~~~~~~~~~~~~
All observational datasets used in the PMP analysis are published through the [ESGF obs4MIPs project](https://esgf-node.llnl.gov/). In addition, several derived climatological products—while not currently available via ESGF—can be accessed directly via download.

To obtain the reference climatologies used in the PMP mean climate metrics, download the list of datasets from:
https://pcmdi.llnl.gov/pss/pmpdata/PMP_obs4MIPsClims_v20250228.txt

Instructions for downloading and using these reference climatologies are provided in [Demo notebook 1b](http://pcmdi.github.io/pcmdi_metrics/examples/Demo_1b_mean_climate.html).