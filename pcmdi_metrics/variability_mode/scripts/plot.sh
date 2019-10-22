#!/bin/bash

# Temporary example to run plot

set -ax

mode='NAM'
#mode='NAO'
#mode='SAM'
#mode='PNA'

#for mode in 'NAM' 'NAO' 'SAM' 'PNA'; do
  python -i read_json_plot_charts.py -j '../'$mode'/var_mode_'$mode'_eof1_stat_cmip5_historical_r1i1p1_mo_atm_1900-2005.json' -s 'all' -v 'psl' -e 'cmip5' -m $mode
#done

mode='PDO'
season='monthly'

#python -i read_json_plot_charts.py -j '../'$mode'/var_mode_'$mode'_eof1_stat_cmip5_historical_r1i1p1_mo_atm_1900-2005.json' -s $season -v 'psl' -e 'cmip5' -m $mode
