.. title:: PMP Monsoon

.. _Monsoon-example:

*****************
Monsoon
*****************

Overview
========

The PMP currently can be used to produce baseline metrics on the overall pattern and evolution of regional monsoons.

Spatial pattern
~~~~~~~~~~~~~~~

These pattern results are based on the work of Wang et al. (2011), examining the annual cycle of precipitation in observations 
and CMIP for six monsoon-related domains.


Temporal evolution
~~~~~~~~~~~~~~~~~~

These evolution results are based on the work of Sperber and Annamalai (2014).  
Climatological pentads of precipitation in observations and CMIP5 for six monsoon-related domains 
(AIR: All-India Rainfall, AUS: Australian Monsoon, GoG: Gulf of Guinea, NAM: North American Monsoon, 
SAM: South American Monsoon, and Sahel). In the Northern Hemisphere the 73 climatological pentads run 
from January-December, while in the Southern Hemisphere the climatological pentads run from July-June. 
For each domain the precipitation is accumulated at each subsequent pentad and then divided by the total 
precipitation to give the fractional accumulation of precipitation as a function of pentad. 
Except for GoG, onset (decay) of monsoon occurs for a fractional accumulation of 0.2 (0.8). 
Between these fractional accumulations the accumulation of precipitation is nearly linear as the monsoon season progresses.

Demo
====
* `PMP demo Jupyter notebook (spatial pattern)`_ (Wang et al. 2011)
* `PMP demo Jupyter notebook (temporal evolution)`_ (Sperber and Annamalai 2014)

References
==========
* Wang, B., Kim, HJ., Kikuchi, K. et al. 2011. Diagnostic metrics for evaluation of annual and diurnal cycles. Clim Dyn 37, 941–955. https://doi.org/10.1007/s00382-010-0877-0
* Sperber, K.R. and Annamalai, H., 2014. The use of fractional accumulated precipitation for the evaluation of the annual cycle of monsoons. Climate Dynamics, 43, 3219-3244, https://doi.org/10.1007/s00382-014-2099-3

.. _PMP demo Jupyter notebook (spatial pattern): examples/Demo_2a_monsoon_wang.html
.. _PMP demo Jupyter notebook (temporal evolution): examples/Demo_2b_monsoon_sperber.html

