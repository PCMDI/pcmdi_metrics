# Jupyter notebook demos

These notebooks provide some basic examples for running the PMP metrics modules. They demonstrate how to use both input parameter files and the command line to generate metrics. Parameter files are generated from the \*.py.in templates by running the Demo_0_download_data.ipynb notebook.

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
The notebooks listed below contain command line examples that can be copied from the notebook, customized, and run in the terminal. These commands are found in cells with a *%%bash* header.

## What's in the notebooks
[Demo 0](https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_0_download_data.ipynb): Set data and output directories. Download sample data and use cdscan to create xml. Generate parameter files.
[Demo 1](https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_1_mean_climate.ipynb): Run the Mean Climate driver and explore the many options for customization.
[Demo 1a](https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_1a_compute_climatologies.ipynb): Learn how to create annual climatology files for running the mean climate driver with custom data.
[Demo 2a](https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_2a_monsoon_wang.ipynb): Run the Monsoon (Wang) driver and its options.
[Demo 2b](https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_2b_monsoon_sperber.ipynb): Run the Monsoon (Sperber) driver with options. Maps the monsoon regions and displays output graphic.
[Demo 3](https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_3_diurnal_cycle.ipynb): Demonstrates the full workflow for running the Diurnal Cycle metrics.
[Demo 4](https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_4_modes_of_variability.ipynb): Install scipy and eofs in the kernel environment, run the modes of variability driver with the NAM, and view an output image.
[Demo 5](https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_5_mjo_metrics.ipynb): Run the MJO driver with options and view an output image.
