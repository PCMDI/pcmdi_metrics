.. title:: PMP API

API Reference
=============

APIs
----

.. currentmodule:: pcmdi_metrics

Below is a list of Application Programming Interfaces (APIs) available in `pcmdi_metrics (> v3.6.1)`.


Custom calendars
~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.custom_season_average
    utils.custom_season_departure
    utils.replace_date_pattern


Data load
~~~~~~~~~
.. autosummary::
    :toctree: generated/

    io.xcdat_open


Date
~~~~
.. autosummary::
    :toctree: generated/

    utils.date_to_str
    utils.extract_date_components
    utils.find_overlapping_dates


Land-sea mask
~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.create_land_sea_mask
    utils.apply_landmask
    utils.apply_oceanmask


Graphics
~~~~~~~~

Example usages of the following plotting functions are available in the `demo notebooks <demo-notebooks.html#plots>`_.

.. autosummary::
    :toctree: generated/

    graphics.parallel_coordinate_plot
    graphics.portrait_plot
    graphics.TaylorDiagram


Grid and regrid
~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.create_target_grid
    utils.regrid


Region handling
~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    io.load_regions_specs
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


Quality control (QC) and repair
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.check_daily_time_axis
    utils.check_monthly_time_axis
    utils.regenerate_time_axis
    

Miscellaneous tools
~~~~~~~~~~~~~~~~~~~
.. autosummary::
    :toctree: generated/

    utils.sort_human
    utils.fill_template
    utils.tree


Viewer
~~~~~~

Viewer will be available in `pcmdi_metrics (> v3.9.1)`.

.. autosummary::
    :toctree: generated/

    viewer.generate_pmp_output_viewer_multimodel