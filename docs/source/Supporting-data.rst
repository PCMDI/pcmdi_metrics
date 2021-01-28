.. _using-the-package:

*****************
Retrieving data for demos and use of the PMP
*****************

Options for downloading
========

Sample model and observational data are provided via a `jupyter notebook demo <https://github.com/acordonez/pcmdi_metrics/blob/645_notebooks/doc/jupyter/Demo/Demo_0_download_data.ipynb>`_.

For users that are unfamiliar with Jupyter notebooks or just want to download the sample data, you can save and run the attached script.





But if you are curious, the key bits of python in the script above are repeated below. :: 

    import requests
    r = requests.get("https://pcmdiweb.llnl.gov/pss/pmpdata/cmec_tutorial_files.txt")
    with open("data_files.txt","wb") as f:
       f.write(r.content)

To retrieve these sample files locally, one first sets the location where they want the demo data to be stored locally. ::

    demo_data_directory = 'MyDemoPath' 


The last line sets the demo_output directories. After that, data is downloaded as follows: ::

    import cdat_info
    cdat_info.download_sample_data_files("data_files.txt", demo_data_directory)



