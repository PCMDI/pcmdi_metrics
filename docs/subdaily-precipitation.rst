.. _subdaily-precipitation:

***********************
Sub-daily precipitation
***********************

Overview
========

The PMP can be used to compare observed and simulated sub-daily precipition, including forced (the diurnal and semi-diurnal cycle) and unforced variability (often referred to as "intermittency").  Well established Fourier analysis (e.g., Dai, 2006) with well-established large scale objective performance metrics (Covey et al., 2016) to estimate the phase and amplitude of the diurnal and semi-diurnal cycle of precipitation.  The unforced sub-daily variability stems from methods developed by Trenberth et al. (2017) and Covey et al. (2017).  Both analysis require data at a 3hr time resolution.   

Analysis of higher frequency data often includes multiple stages of processing.  `The flow diagram of the PMP's sub-daily precipitation <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/Diurnal%20Cycle%20Diagram.pdf>`_ shows that is the case here.  Each of the steps highlighted in the flow diagram are included in `the diurnal cycle and intermittency Jupyter notebook demo <https://github.com/PCMDI/pcmdi_metrics/blob/master/doc/jupyter/Demo/Demo_3_diurnal_cycle.ipynb>`_. 


References
==========

Covey, C, PJ Gleckler, C Doutriaux, DN Williams, A Dai, J Fasullo, K Trenberth, and A Berg. 2016. ”Metrics for the diurnal cycle of precipitation: Toward routine benchmarks for climate models.” Journal of Climate 29(12): 4461–4471, https://doi.org/10.1175/JCLI-D-15-0664.1

Covey, C, C Doutriaux, PJ Gleckler, KE Taylor, KE Trenberth, and Y Zhang. 2018. “High-frequency intermittency in observed and model-simulated precipitation.” Geophysical Research Letters 45(22): 12514–12522, https://doi.org/10.1029/2018GL078926

Dai, A. 2006. “Precipitation characteristics coupled climate models.” Journal of Climate 19(18): 4605–4630, https://doi.org/10.1175/JCLI3884.1

Trenberth, KE, Y Zhang, and M Gehne. 2017. ”Intermittency in precipitation: Duration, frequency, intensity, and amounts using hourly data.” Journal of Hydrometeorology 18(5): 1393–1412, https://doi.org/10.1175/JHM-D-16-0263.1
