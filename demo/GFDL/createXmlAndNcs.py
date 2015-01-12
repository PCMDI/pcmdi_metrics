#!/home/p1d/140922_metrics/PCMDI_METRICS/bin/python

"""
Created on Tue Jan 28 14:07:12 2014

Paul J. Durack 28th January 2014

This script scans netcdf files to create a composite xml spanning file
and then using this index file, writes netcdf files for each variable

PJD 28 Jan 2014     - Completed 6 variables following changes to metrics code
PJD 29 Jan 2014	    - Added additional atmos variables for processing
PJD 29 Jan 2014     - Updated shebang statement for latest uvcdat build
PJD 29 Jan 2014     - Corrected input for psl outvar to slp (different from cmip5 files)
PJD 29 Jan 2014     - Updated model_period format YYYY -> YYYYMM
PJD 29 Jan 2014     - Updated experiment to historical
PJD 25 Mar 2014     - Updated to deal with ocean and atmos vars
PJD 26 Mar 2014	    - Added axis aliases to deal with non-standard dimension names
PJD 18 Apr 2014     - Updated build shebang
PJD 25 Apr 2014     - Updated to latest build
PJD 17 May 2014     - Updated to latest build
PJD  5 Aug 2014     - Updated to latest build
PJD  8 Aug 2014     - Updated to latest build (numpy 1.9.0b1)
PJD 15 Aug 2014	    - Updated to latest build (UV-CDAT v2.0 beta default)
PJD 28 Aug 2014     - Updated to latest build (UV-CDAT v2.0 beta default/metrics master branch)
PJD  2 Sep 2014     - Updated to latest build (UV-CDAT v2.0 beta default/metrics devel branch)
PJD 22 Sep 2014     - Updated to latest build (including VCS/portraits)
PJD 24 Sep 2014     - Updated to include GFDL-CM4 data

@author: durack1
"""

import os,string,subprocess,sys
import cdms2 as cdm

# Set cdms preferences - no compression, no shuffling, no complaining
cdm.setNetcdfDeflateFlag(0)
cdm.setNetcdfDeflateLevelFlag(0)
cdm.setNetcdfShuffleFlag(0)
cdm.setCompressionWarnings(0)
#cdm.axis.level_aliases.append('zt') ; # Add zt to axis list
#cdm.axis.latitude_aliases.append('yh') ; # Add yh to axis list
#cdm.axis.longitude_aliases.append('xh') ; # Add xh to axis list
# Set bound automagically
#cdm.setAutoBounds(1) ; # Use with caution

# Set build info once
buildDate = '140922'

# Create input variable lists 
uvcdatInstall = ''.join(['/home/p1d/',buildDate,'_metrics/PCMDI_METRICS/bin/'])
data = [
	['ocean','GFDL-ESM2G','*0001-0100*','/archive/esm2g/fre/postriga_esm_20110506/ESM2G/ESM2G_pi-control_C2/gfdl.default-prod/pp/ocean_z/av/monthly_100yr/'],
	['ocean','GFDL-CM4','*0001-0005*','/archive/jpk/mdt/20140829/tikal_201403_awgUpdates_mom6_2014.08.29/CM4i_c96L48_am4a1r1_1860forc/gfdl.ncrc2-default-prod-openmp/pp/ocean_z/av/monthly_5yr/'],
	['atmos','GFDL-ESM2G','*0001-0100*','/archive/esm2g/fre/postriga_esm_20110506/ESM2G/ESM2G_pi-control_C2/gfdl.default-prod/pp/atmos/av/monthly_100yr/'],
	['atmos','GFDL-CM4','*0001-0005*','/archive/jpk/mdt/20140829/tikal_201403_awgUpdates_mom6_2014.08.29/CM4i_c96L48_am4a1r1_1860forc/gfdl.ncrc2-default-prod-openmp/pp/atmos/av/monthly_5yr/']
]
inVars = [['temp'],['hght','olr','olr_clr','precip','slp','swup_toa','swup_toa_clr','t_ref','temp','u_ref','ucomp','v_ref','vcomp']]
outVars = [['tos'],['zg','rlut','rlutcs','pr','psl','rsut','rsutcs','tas','ta','uas','ua','vas','va']]

for count1,realm in enumerate(data):
	realmId 	= realm[0]
	modelId 	= realm[1]
	timeAve		= realm[2]
	dataPath	= realm[3]
	#print realmId,modelId,dataPath
	# Create input xml file
	command = "".join([uvcdatInstall,'cdscan -x test_',modelId,'_',realmId,'.xml ',dataPath,timeAve,'.nc'])
	#print command
	fnull = open(os.devnull,'w') ; # Create dummy to write stdout output
	p = subprocess.call(command,stdout=fnull,shell=True)
	fnull.close() ; # Close dummy
	print 'XML spanning file created for model/realm:',modelId,realmId
	#sys.exit()

	# Open xml file to read
	infile = ''.join(['test_',modelId,'_',realmId,'.xml'])
	#print infile
	fIn = cdm.open(infile)
	
	# Deal with variables
	if count1<2:
		realmIndex = 0
	else:
		realmIndex = 1
	inVarList 	= inVars[realmIndex]
	outVarList 	= outVars[realmIndex]
	
	# Create output netcdf files
	for count2,var in enumerate(inVarList):
		#print var
		varRead = inVarList[count2]
		varWrite = outVarList[count2]
		#print varRead,varWrite
		if realmId == 'atmos':
			tableId = 'Amon'
		else:
			tableId = 'Omon'	
		data = fIn(varRead)
		data.id = varWrite
		print "".join(['** Writing variable: ',varRead,' to ',varWrite,' **'])
		#outfile = ".".join(['cmip5.GFDL-ESM2G.piControl.r1i1p1.mo',tableId,varWrite,'ver-1.latestX.000101-010012.AC.nc'])
		outfile = "_".join([varWrite,modelId,tableId,'historical_r1i1p1_01-12-clim.nc'])
		print "".join(['** Writing file:    ',outfile])
		if os.path.isfile(outfile):
			os.remove(outfile) ; # purge existing file
		fOut = cdm.open(outfile,'w')
		for ax in data.getAxisList():
			#print ax,ax.isLevel()
			if ax.isLevel() and realmId == 'atmos':
             			ax[:]=ax[:]*100.
             			ax.units = 'Pa'
			if ax.isLevel() and realmId == 'ocean':
				#print data.shape
				data = data[:,0,:,:] ; # Trim to top layer - thetao -> tos
				#print data.shape
				data.id = 'tos' ; # rename to tos
		fOut.write(data)
		fOut.close()
	fIn.close()

# Execute shell command
# source /home/p1d/140922_metrics/PCMDI_METRICS/bin/setup_runtime.csh
# > pcmdi_metrics_driver.py -p gfdl_input_parameters_test.py
