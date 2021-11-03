#####
# CONVERT NCAR CLIMATOLOGIES TO BE CONSISTENT WITH CMIP STRUCTURE FOR PMP USE
# PLANNED IMPROVEMENTS:
#    CURRENTLY ASSUMES cdscan XML FILES HAVE BEEN CREATED IN ADVANCE
#    CURRENTLY ASSUMES LOCATION OF XML FILES AND PRODUCES CLIMS FOR ALL SIMULATIONS WITH XMLS
#    CURRENTLY HAS OUTPUT "data" DIRECTORY
#    argparse WILL BE USED TO SELECT ALL OF THE ABOVE VIA COMMAND LINE EXECUTION

#    CMOR WILL BE USED TO WRITE CLIMATOLGIES - Time/bounds CURRENTLY HARDWIRED
##### LAST UPDATE 6/29/16 PJG


import cdms2 as cdms
import os, string
import MV2 as MV
import cdutil
import sys

# Set cdms preferences - no compression, no shuffling, no complaining
cdms.setNetcdfDeflateFlag(1)
cdms.setNetcdfDeflateLevelFlag(9) ; # 1-9, min to max - Comes at heavy IO (read/write time cost)
cdms.setNetcdfShuffleFlag(0)
cdms.setCompressionWarnings(0) ; # Turn off nag messages
# Set bounds automagically
#cdms.setAutoBounds(1) ; # Use with caution


### DICTIONARY MAPPING NCAR AND CMIP VARIABLE ID'S
ncar_cmip_direct_name_map = {'psl':'PSL','tas':'TREFHT','huss':'QREFHT','ua':'U','va':'V','ta':'T','pr':'PRECC','rlut':'FSNTOA','rsut':'SOLIN','rlutcs':'FLUTC','rsutcs':'FSNTOAC','rsds':'FSDS','rlds':'FLDS','prw':'TMQ','zg':'Z3','tauu':'TAUX','tauv':'TAUY','swcre':'swcf'}


#  Code currently

lst1 = os.popen('ls xmls/*.xml').readlines()

lst = []
for l in lst1:
# if string.find(l,'FAMIPC5_ne120_79to05_03_omp2') == -1:
     lst.append(l)

#lst = os.popen('ls xmls/f.e11.FAMIPC5.f19_f19.topo_2d_control.001.xml')

vars = ['psl','tas','ua','va','pr','rlut','prw','zg','tauu','tauv']
vars = ['rsutcs']
#vars = ['rlutcs','rsdtcs','rsds','rlds']

# CLIMATOLOGY TIME MODEL

timel = [15.5, 45.5, 75.5, 106, 136.5, 167, 197.5, 228.5, 259, 289.5, 320, 350.5]
timelbds =  [(0, 31), (31, 60), (60, 91), (91, 121), (121, 152), (152, 182,), (182, 213), (213, 244), (244, 274), (274, 305), (305, 335), (335, 366)]
ta = cdms.createAxis(timel,id='time')
tb = MV.array(timelbds)
tb = tb.astype('float64')
ta.setBounds(tb)
ta.climatology = "climatology_bnds"
ta.units = "days since 0"
ta.calendar = 'gregorian'
ta.axis = 'T'
ta.long_name = 'time'
ta.standard_name = 'time'


print 'BEGIN PROCESSING...'

for l in lst:
    l = l[:-1]

    f = cdms.open(l)

# TRAP EXP NAME
    tmp1 = string.split(l,'/')[1]
    expname = string.split(tmp1,'.xml')[0]

    try:
     os.mkdir('data/' + expname)
    except:
     pass
    try:
     dirout = 'data/' + expname
    except:
     pass

    for var in vars:
       var_ncar = ncar_cmip_direct_name_map[var]
       d = f(var_ncar)

       if var in ['ua','va','ta']:
          ps1=f('PS')
          po1=f('P0')
          ha1=f('hyam')
          hb1=f('hybm')
          print 'before vertical interpolation of ', var,'  ', `d.shape`
          p1=cdutil.vertical.reconstructPressureFromHybrid(ps1,ha1,hb1,po1)
          dall = cdutil.vertical.linearInterpolation(d,p1)
          print 'finished vertical interpolation of ', var
          levs = dall.getLevel()
          print levs
          d = MV.multiply(dall(level = slice(0,2)),0.)
          d1 = dall(level=(85000,85000))
          d2 = dall(level=(20000,20000))
          d[:,0,:,:] = d1[:,0,:,:]
          d[:,1,:,:] = d2[:,0,:,:]
          levs = [85000.,20000.]
          levs_tv = cdms.createAxis(levs,id = 'level')
          levs_tv.units = 'Pa'
          levs_tv.axis = 'Z'
          d.setAxis(1,levs_tv)

       if var in ['zg']:
          ps1=f('PS')
          po1=f('P0')
          ha1=f('hyam')
          hb1=f('hybm')
          print 'before vertical interpolation of ', var,'  ', `d.shape`
          p1=cdutil.vertical.reconstructPressureFromHybrid(ps1,ha1,hb1,po1)
          dall = cdutil.vertical.linearInterpolation(d,p1)
          print 'finished vertical interpolation of ', var
          levs = dall.getLevel()
          print levs
          d = MV.multiply(dall(level = slice(0,1)),0.)
          d1 = dall(level=(50000,50000))
          d[:,0,:,:] = d1[:,0,:,:]
          levs = [50000.]
          levs_tv = cdms.createAxis(levs,id = 'level')
          levs_tv.units = 'Pa'
          levs_tv.axis = 'Z'
          d.setAxis(1,levs_tv)

       if var == 'pr':
           d1 = f('PRECL')
           d = (d + d1)*1000.
           d.units = 'kg m-2 s-1'

       if var == 'rlut':
           d1  = f('FSNTOA')
           d2   = f('FSNT')
           d3   = f('FLNT')
           d    = d1-d2+d3 ; #FSNTOA - FSNT + FLNT
           d.id = 'rlut'
           d.long_name = 'toa_outgoing_longwave_flux'
           d.history = 'Converted to RLUT from FSNTOA - FSNT + FLNT'
           d.units  = d.units

       if var == 'rsut':
           d1  = f('SOLIN')
           d2   = f('FSNTOA')
           d    = d1-d2 ; #FSNTOA - FSNT + FLNT
           d.id = 'rsut'
           d.long_name = 'toa_reflected_shortwave_flux'
           d.history = 'Converted to RSUT from SOLIN - FSNTOA'
           d.units  = d.units

       if var == 'rsutcs':
           d1  = f('SOLIN')
           d2   = f('FSNTOAC')
           d    = d1-d2 ; #FSNTOA - FSNT + FLNT
           d.id = 'rsutcs'
           d.long_name = 'toa_reflected_shortwave_flux clear sky'
           d.history = 'Converted to RSUT from SOLIN - FSNTOA clear sky'
           d.units  = d.units

       print f,'  ', var_ncar, '  ', d.shape

       d.id = var
       d.setAxis(0,ta)


       g = cdms.open(dirout + '/' + var + '.nc','w+')
       g.write(d)
       g.close()
    f.close()



