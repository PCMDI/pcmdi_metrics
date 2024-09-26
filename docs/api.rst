API Reference
=============

APIs for Developers
-------------------

.. currentmodule:: pcmdi_metrics

Below is a list of APIs available in `pcmdi_metrics (> v3.6)` for developers.


Land-sea mask
~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.create_land_sea_mask
    utils.apply_landmask
    utils.apply_oceanmask


Grid and regrid
~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.create_target_grid
    utils.regrid


Custom calendars
~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.custom_season_average
    utils.custom_season_departure


Region handling
~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    io.region_subset
    io.region_from_file


Retrieve data from xarray Dataset
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    io.get_grid
    io.get_axis_list
    io.get_data_list
    io.get_latitude
    io.get_latitude_bounds
    io.get_latitude_key
    io.get_longitude
    io.get_longitude_bounds
    io.get_longitude_key
    io.get_time
    io.get_time_bounds
    io.get_time_bounds_key
    io.get_time_key
    io.select_subset


Quality control (QC)
~~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.check_daily_time_axis
    utils.check_monthly_time_axis
    

Miscellaneous tools
~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.sort_human
    utils.fill_template
    utils.tree
