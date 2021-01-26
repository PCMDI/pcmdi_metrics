# Jupyter notebook demos  

These notebooks provide some basic examples for 3 PMP modules (mean climate, monsoon (wang), and diurnal cycle). They demonstrate how to use both parameter files and the command line to generate metrics. Parameter files are generated from the \*.py.in templates by running the Demo_0_download_data.ipynb notebook.

## Environment  
PCMDI metrics package should be installed. Consult [the documentation](http://pcmdi.github.io/pcmdi_metrics/install-using-anaconda.html) for more help.   

To run the notebooks directly, the user should install [jupyter notebook software](https://jupyter.org/install). Additionally, the user should clone the PMP to acquire the notebooks:  
`git clone https://github.com/PCMDI/pcmdi_metrics.git`  

## Running the notebooks  
From pcmdi_metrics, launch the jupyter notebook server:  
`cd pcmdi_metrics/doc/jupyter/Demo/`  
`jupyter notebook`  

If the notebook is being run on a remote server, [set up an SSH tunnel](https://docs.anaconda.com/anaconda/user-guide/tasks/remote-jupyter-notebook/) to view it locally.  

The jupyter dashboard will be launched in your browser. From there, navigate to Demo_0_download_data.ipynb. This notebook must be run first because it populates the demo data and parameter files for the later demos. The other notebooks can be run in any order. For more help with running notebooks, consult the [documentation](https://jupyter.readthedocs.io/en/latest/running.html#running).  

## Copying commands from notebooks  
The mean climate notebook contains command line examples that can be copied from the notebook, customized, and run in the terminal. These commands are found in cells with a *%%bash* header.
