#!/glade/u/home/durack1/141104_metrics/PCMDI_METRICS/bin/python

"""
Created on Mon Nov 24 14:58:07 2014

Paul J. Durack 24th November 2014

This script scans netcdf files to create a composite xml spanning file
and then using this index file, writes netcdf files for each variable

PJD 24 Nov 2014     - Began script
PJD 24 Nov 2014     - Updated to include GFDL-CM4 data

@author: durack1
"""

import os,subprocess,sys
import cdms2 as cdm

# Set cdms preferences - no compression, no shuffling, no complaining
cdm.setNetcdfDeflateFlag(0)
cdm.setNetcdfDeflateLevelFlag(0)
cdm.setNetcdfShuffleFlag(0)
cdm.setCompressionWarnings(0)
#cdm.axis.level_aliases.append('zt') ; # Add zt to axis list
#cdm.axis.latitude_aliases.append('yh') ; # Add yh to axis list
#cdm.axis.longitude_aliases.append('xh') ; # Add xh to axis list
# Set bounds automagically
#cdm.setAutoBounds(1) ; # Use with caution

# Set build info once
buildDate = '141104'

# Create input variable lists 
uvcdatInstall = ''.join(['/glade/u/home/durack1/',buildDate,'_metrics/PCMDI_METRICS/bin/'])
data =  [
        ['atmos','CAM5_1deg','f.e12.FAMIPC5.ne30_g16.amip.002_*','/glade/p/cgd/amp/people/hannay/amwg/climo/f.e12.FAMIPC5.ne30_g16.amip.002/0.9x1.25/'],
        ['atmos','CAM5_0p25deg','FAMIPC5_ne120_79to05_03_omp2_*','/glade/p/cgd/amp/people/hannay/amwg/climo/FAMIPC5_ne120_79to05_03_omp2/0.23x0.31/'],
        ['atmos','CAM5_0p25deg_interp_1deg','FAMIPC5_ne120_79to05_03_omp2_','/glade/p/cgd/amp/people/hannay/amwg/climo/FAMIPC5_ne120_79to05_03_omp2/0.9x1.25/']
]
inVarsAtm   = ['','QREFHT','','TMQ','PSL','FLDS','FLDSC','','FLUTC','FSDS','FSDSC','SOLIN','','TREFHT','TAUX','TAUY','','','','','']
outVarsAtm  = ['hus','huss','pr','prw','psl','rlds','rldscs','rlut','rlutcs','rsds','rsdscs','rsdt', \
               'ta','tas','tauu','tauv','ua','uas','va','vas','zg']
inVarsOcn   = ['SALT','TEMP','SSH']
outVarsOcn  = ['sos','tos','zos']
varMatch    = ['hus','pr','rlut','ta','ua','uas','va','vas','zg']
varCalc     = [[['Q','PS'],'Q interpolated to standard plevs'],[['PRECC','PRECL'],'PRECC + PRECL and unit conversion'],[['FSNTOA','FSNT','FLNT'],'FSNTOA-FSNT+FLNT'],[['T','PS'],'T interpolated to standard plevs'],[['U','PS'],'U interpolated to standard plevs'],[],[['V','PS'],'V interpolated to standard plevs'],[],[['Z3','PS'],'Z3 interpolated to standard plevs']]

#%%
'''
for x,var in enumerate(outVarsAtm):
    if inVarsAtm[x] == '':
        index = varMatch.index(var)
        print var.rjust(6),':',varCalc[index]
    else:
        print var.rjust(6),':',inVarsAtm[x]

'''
#%%
# Loop through input data
for count1,realm in enumerate(data):
	realmId    = realm[0]
	modelId    = realm[1]
	fileId     = realm[2]
	dataPath   = realm[3]
	print realmId,modelId,dataPath
	# Create input xml file
	command = "".join([uvcdatInstall,'cdscan -x test_',modelId,'_',realmId,'.xml ',dataPath,fileId,'[0-9]*.nc'])
	print command
	fnull = open(os.devnull,'w') ; # Create dummy to write stdout output
	p = subprocess.call(command,stdout=fnull,shell=True)
	fnull.close() ; # Close dummy
	print 'XML spanning file created for model/realm:',modelId,realmId
	sys.exit()

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
# > pcmdi_metrics_driver.py -p pcmdi_input_parameters_test.py
