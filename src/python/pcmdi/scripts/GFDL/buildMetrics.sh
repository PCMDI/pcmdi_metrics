#!/bin/tcsh

# File written to create new dir and clone metrics git repo

# Paul J. Durack 29th January 2014

# PJD 29 Jan 2014	- Install script written for new installation
# PJD 29 Jan 2014       - Added test for directory existence
# PJD 18 Apr 2014	- Added edit to build from devel branch
# PJD 17 May 2014       - Added UV-CDAT environment configure to end
# PJD 28 Aug 2014 	- Converted to master branch (was devel)
# PJD  2 Sep 2014       - Updated to devel branch, get unit hard code and csh fixes

set date=`date +%y%m%d`
set dir=/home/p1d/${date}_metrics
echo $dir
if ( -d $dir ) then
   echo "$dir exists, exiting.."
   exit 0
endif
rm -rf ${dir}
mkdir ${dir}
echo
echo "$dir built.."
echo
cd ${dir}
#\git clone -b devel git://github.com/PCMDI/pcmdi_metrics.git ; # Clone devel branch
#\git clone -b master git://github.com/PCMDI/pcmdi_metrics.git ; # Clone master branch
\wget -vv --no-check-certificate https://raw.githubusercontent.com/PCMDI/pcmdi_metrics/devel/install_metrics.bash
echo
echo "pcmdi_metrics repo cloned.."
echo
# Prepare to build
#cp pcmdi_metrics/install_metrics.bash .
#echo
#echo "Editing to build from devel branch"
#find -name install_metrics.bash -print -exec sed -i.bak 's/metrics_checkout=\"master\"/metrics_checkout=\"devel\"/g'
#echo
#echo "Devel branch edit complete
#echo
echo "installing UV-CDAT.."
echo
\bash install_metrics.bash
# Add install to path
#setenv PATH "$dir/WGNE/bin":$PATH

# Configure UV-CDAT environment
source "${dir}/PCMDI_METRICS/bin/setup_runtime.csh
which python
which pcmdi_metrics_driver.py
