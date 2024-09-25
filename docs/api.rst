API Reference
=============

API Functions for Developpers
-----------------------------

.. currentmodule:: pcmdi_metrics

Below is a list of some API functions that are available in `pcmdi_metrics.` for developpers.


Land-sea mask
~~~~~~~~~~~~~

.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.create_land_sea_mask
    pcmdi_metrics.utils.apply_landmask
    pcmdi_metrics.utils.apply_oceanmask


Grid handling and re-gridding (horizontal interpolation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.create_target_grid
    pcmdi_metrics.utils.regrid
    

Quality control (QC)
~~~~~~~~~~~~~~~~~~~~

.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.check_daily_time_axis
    pcmdi_metrics.utils.check_monthly_time_axis


Calendar-related functions
~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.custom_season_average
    pcmdi_metrics.utils.custom_season_departure


Miscellaneous tools
~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    pcmdi_metrics.utils.sort_human
    pcmdi_metrics.utils.fill_template
    pcmdi_metrics.utils.tree


Region handling
~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    pcmdi_metrics.io.region_subset
    pcmdi_metrics.io.region_from_file


Retrieve data from xarray Dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    pcmdi_metrics.io.get_grid
    pcmdi_metrics.io.get_axis_list
    pcmdi_metrics.io.get_data_list
    pcmdi_metrics.io.get_latitude
    pcmdi_metrics.io.get_latitude_bounds
    pcmdi_metrics.io.get_latitude_key
    pcmdi_metrics.io.get_longitude
    pcmdi_metrics.io.get_longitude_bounds
    pcmdi_metrics.io.get_longitude_key
    pcmdi_metrics.io.get_time
    pcmdi_metrics.io.get_time_bounds
    pcmdi_metrics.io.get_time_bounds_key
    pcmdi_metrics.io.get_time_key
    pcmdi_metrics.io.select_subset
    
