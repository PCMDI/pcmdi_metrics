.. title:: PMP Demo Notebooks
.. _metrics-demo:

**************
Demo notebooks
**************

Metrics
~~~~~~~

We provide demo notebooks to help users get started with the PMP. 
Most demos are straightforward examples showing how to apply the PMP to one or more datasets. 
For more advanced use cases (such as running the PMP across all CMIP models), 
we include example parameter files based on PCMDI's semi-operational setup for the CMIP database. 
Overviews for metrics can be found `here <metrics.html>`_. 

To make it easier to run these demos, we recommend cloning the `PMP GitHub repository <https://github.com/PCMDI/pcmdi_metrics>`_, and run them in the environment where PMP is `installed <install.html>`_.

.. code-block::

   $ clone https://github.com/PCMDI/pcmdi_metrics.git
   $ cd pcmdi_metrics/doc/jupyter/Demo


.. nbgallery::
   :caption: Demo notebooks:

   examples/Demo_0_download_data
   examples/Demo_1a_compute_climatologies
   examples/Demo_1b_mean_climate
   examples/Demo_2a_monsoon_wang
   examples/Demo_2b_monsoon_sperber
   examples/Demo_3_diurnal_cycle
   examples/Demo_4_modes_of_variability
   examples/Demo_5_mjo_metrics
   examples/Demo_6_ENSO
   examples/Demo_7_precip_variability
   examples/Demo_8_extremes
   examples/Demo_9_seaIceExtent_ivanova
   examples/Demo_9b_seaIce_data_explore


Plots
~~~~~

We also provide demo notebooks showcasing PMP's plotting capabilities, and the `API reference <api.html#graphics>`_ includes detailed information on the available parameters for PMP's plotting functions.

Basic Usage Examples
^^^^^^^^^^^^^^^^^^^^

.. nbgallery::

   examples/portrait_plot_example
   examples/parallel_coordinate_plot_example
   examples/taylor_diagram_example

Practical Use Cases
^^^^^^^^^^^^^^^^^^^

.. nbgallery::

   examples/portrait_plot_mean_clim
   examples/portrait_plot_mean_clim_multiple_CMIPs
   examples/parallel_coordinate_plot_mean_clim
   examples/parallel_coordinate_plot_mean_clim_multiMIPs
   examples/taylor_diagram_multiple_CMIPs
   examples/mean_clim_plots_test_model
   examples/variability_modes_plots_all-stats
   examples/return_value_portrait_plot_demo


Data analysis and support
~~~~~~~~~~~~~~~~~~~~~~~~~

.. nbgallery::

   examples/landmask
   examples/pmp_metrics_database