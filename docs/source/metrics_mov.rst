***********************************
Extra-tropical modes of variability
***********************************

Overview
========

PMP calculates skill metrics for extra-tropical modes of variability (EMoV), including 
the Northern Annular Model (NAM), the North Atlantic Oscillation (NAO), 
the Southern Annular Mode (SAM), the Pacific North American pattern (PNA), 
the North Pacific Oscillation (NPO), the Pacific Decadal Oscillation (PDO), 
and the North Pacific Gyre Oscillation (NPGO). 

For NAM, NAO, SAM, PNA, and NPO the results are based on sea-level pressure, 
while the results for PDO and NPGO are based on sea surface temperature. 
Our approach distinguishes itself from other studies that analyze modes of variability 
in that we use the Common Basis Function approach (CBF), in which model anomalies 
are projected onto the observed modes of variability, together with 
the traditional EOF approach. 

Using the Historical simulations, the skill of the spatial patterns is given by 
the Root-Mean-Squared-Error (RMSE), and the Amplitude gives the standard deviation 
of the Principal Component time series.

Demo
====
* `PMP demo Jupyter notebook`_

Results
=======
* `Interactive graphics for PMP-calculated MoV Metrics`_
* `Description for the results`_

References
==========
* Lee, J., K. Sperber, P. Gleckler, C. Bonfils, and K. Taylor, 2019: Quantifying the Agreement Between Observed and Simulated Extratropical Modes of Interannual Variability. Climate Dynamics, 52, 4057-4089, https://doi.org/10.1007/s00382-018-4355-4
* Lee, J., K. Sperber, P. Gleckler, K. Taylor, and C. Bonfils, 2021: Benchmarking performance changes in the simulation of extratropical modes of variability across CMIP generations. Journal of Climate, 34, 6945–6969, https://doi.org/10.1175/JCLI-D-20-0832.1


.. _PMP demo Jupyter notebook: https://github.com/PCMDI/pcmdi_metrics/blob/main/doc/jupyter/Demo/Demo_4_modes_of_variability.ipynb
.. _Interactive graphics for PMP-calculated MoV Metrics: https://pcmdi.llnl.gov/pmp-preliminary-results/interactive_plot/variability_modes/portrait_plot/pmp_mov_page_viewer.html
.. _Description for the results: https://pcmdi.llnl.gov/research/metrics/variability_modes/