********************
MJO baseline metrics
********************

Overview
========
The MJO consists of large-scale regions of enhanced and suppressed convection, 
and associated circulation anomalies in the tropics that propagate eastward, 
mainly over the eastern hemisphere, with a time scale of ~30-60 days 
(Madden and Julian `1971`_, `1972`_, `1994`_). Its large-scale nature and period are 
easily seen via frequency-wavenumber decomposition of near-equatorial data 
(10°S to 10°N), which partitions the raw anomalies into eastward and westward 
propagating components and also as a function of frequency (cycles/day). 
The frequency-wavenumber decomposition technique has been widely used to assess 
if models properly represent this basic characteristic of the MJO 
(e.g., `CLIVAR MJO Working Group 2009`_; `Kim et al. 2009`_; `Ahn et al. 2017`_).

Here we apply the frequency-wavenumber decomposition method to precipitation 
from observations (GPCP-based; 1997-2010) and the CMIP5 and CMIP6 Historical 
simulations for 1985-2004. For disturbances with wavenumbers 1-3 and 
frequencies corresponding to 30-60 days it is clear in observations that the 
eastward propagating signal dominates over its westward propagating counterpart. 
Thus, an important metric is the eastward/westward power ratio (EWR) for the 
above-mentioned wavenumbers and frequencies, which is about 2.5 in observations.

The EWR results are based on the work of Ahn et al. (`2017`_). 
Implementation of these and other MJO analysis into the PMP is part of a 
PCMDI collaboration with Prof. Daehyun Kim (University of Washington) and 
the WGNE MJO Task Force.

Demo
====
* `PMP demo Jupyter notebook`_

Results
=======
* `Interactive graphics for PMP-calculated MJO Metrics`_
* `Description for the results`_

References
==========
* Ahn, M.-S., D. Kim, K. R. Sperber, I.-S. Kang, E. Maloney, D. Waliser, H. Hendon, 2017: MJO simulation in CMIP5 climate models: MJO skill metrics and process-oriented diagnosis. Clim. Dynam., 49, 4023-4045. `doi: 10.1007/s00382-017-3558-4 <https://doi.org/10.1007/s00382-017-3558-4>`_.
* CLIVAR Madden-Julian Oscillation Working Group (Waliser, D., K. Sperber, H. Hendon, D. Kim, E. Maloney, M. Wheeler, K. Weickmann,, C. Zhang, L. Donner, J. Gottschalck, W. Higgins, I.-S. Kang, D. Legler, M. Moncrieff, S. Schubert, W. Stern, F. Vitart, B. Wang, W. Wang, and S. Woolnough), 2009: MJO simulation diagnostics. J. Clim., 22, 3006-3029. `doi: 10.1175/2008JCLI2731.1 <https://doi.org/10.1175/2008JCLI2731.1>`_.
* Kim, D., K. R. Sperber, W. S. Stern, D. Waliser, I.-S. Kang, E. Maloney, W. Wang, K. Weickmann, J. Benedict, M. Khairoutdinov, M.-I. Lee, R. Neale, M. Suarez, K. Thayer-Calder, and G. Zhang, 2009: Application of MJO simulation diagnostics to climate models. J. Clim., 22, 6413-6436. `doi: 10.1175/2009JCLI3063.1 <https://doi.org/10.1175/2009JCLI3063.1>`_.

.. _Ahn et al. 2017: https://doi.org/10.1007/s00382-017-3558-4
.. _2017: https://doi.org/10.1007/s00382-017-3558-4

.. _CLIVAR MJO Working Group 2009: https://doi.org/10.1175/2008JCLI2731.1
.. _Kim et al. 2009: https://doi.org/10.1175/2009JCLI3063.1

.. _1971: https://doi.org/10.1175/1520-0469(1971)028%3C0702:DOADOI%3E2.0.CO;2
.. _1972: https://doi.org/10.1175/1520-0469(1972)029%3C1109:DOGSCC%3E2.0.CO;2
.. _1994: https://doi.org/10.1175/1520-0493(1994)122%3C0814:OOTDTO%3E2.0.CO;2

.. _PMP demo Jupyter notebook: https://github.com/PCMDI/pcmdi_metrics/blob/main/doc/jupyter/Demo/Demo_5_mjo_metrics.ipynb
.. _Interactive graphics for PMP-calculated MJO Metrics: https://pcmdi.llnl.gov/pmp-preliminary-results/interactive_plot/mjo/bar_chart/mjo_ewr_cmip5and6_overlap_runs_average_v20200720.html
.. _Description for the results: https://pcmdi.llnl.gov/research/metrics/mjo/