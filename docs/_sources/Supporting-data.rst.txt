.. _using-the-package:

*****************
Retrieving data for demos and use of the PMP
*****************


Sample model and observational data are provided via a `jupyter notebook demo <https://github.com/acordonez/pcmdi_metrics/blob/645_notebooks/doc/jupyter/Demo/Demo_0_download_data.ipynb>`_.

For users that are unfamiliar with Jupyter notebooks or just want to download the sample data, without interactively running the demo, you can download the data by launching python from a PMP environment created from conda.  

you can then enter the following :: 

    import requests
    r = requests.get("https://pcmdiweb.llnl.gov/pss/pmpdata/cmec_tutorial_files.txt")
    with open("data_files.txt","wb") as f:
       f.write(r.content)

You can then specify where you want to store the demo data locally: ::

    demo_data_directory = 'MyDemoPath' 


After you have set the location for the demo_output you can downloaded it by entering the following: ::

    import cdat_info
    cdat_info.download_sample_data_files("data_files.txt", demo_data_directory)

The PMP demo data is used for multiple demos. It is ~300MB. The best way to run these demos is via Jupyter notebooks.



