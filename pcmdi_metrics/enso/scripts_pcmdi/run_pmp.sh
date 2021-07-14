#!/bin/sh
set -a

# Working conda env in Crunchy: pmp_nightly_20180830

ver=`date +"%Y%m%d-%H%M"`

#mips='cmip5 cmip6'
#mips='cmip5'
mips='cmip6'
#mips='CLIVAR_LE'
#mips='obs2obs'

#MCs='ENSO_perf ENSO_tel ENSO_proc'
#MCs='ENSO_perf'
#MCs='ENSO_tel ENSO_proc'
#MCs='ENSO_tel'
MCs='ENSO_proc'

param_dir='../param'

#param_file='my_Param_ENSO.py'
param_file='my_Param_ENSO_PCMDIobs.py'
#param_file='my_Param_ENSO_PCMDIobs_CLIVAR_LE.py'
#param_file='my_Param_ENSO_obs2obs.py'
#param_file='my_Param_ENSO_obs2obs_combinedDataSource.py'

mkdir -p log

for mip in $mips; do
    for MC in $MCs; do
        echo $mip $MC
        enso_driver.py -p $param_dir/$param_file --mip ${mip} --metricsCollection ${MC} >& log/log.${mip}.${MC}.all.v${ver}.txt &
        disown
    done
done
