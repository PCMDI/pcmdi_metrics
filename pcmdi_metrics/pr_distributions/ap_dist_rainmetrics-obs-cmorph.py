#!/usr/bin/python
##########################################################################
### Angeline Pendergrass, January 18 2017.
### Starting from precipitation data, 
### 1. Calculate the distribution of rain
### 2. Plot the change from one climate state to another
### This code is ported from the matlab code shift-plus-increase-modes-demo, originally in matlab. 
### 
### You can read about these methods and cite the following papers about them: 
### Pendergrass, A.G. and D.L. Hartmann, 2014: Two modes of change of the                                                                                                       
###   distribution of rain. Journal of Climate, 27, 8357-8371.                                                                                                                  
###   doi:10.1175/JCLI-D-14-00182.1.                                                                                                                                            
### and the shift and increase modes of response of the rainfall distribution                                                                                                   
### to warming, occuring across ENSO events or global warming simulations.                                                                                                      
### The response to warming is described in:                                                                                                                                    
### Pendergrass, A.G. and D.L. Hartmann, 2014: Changes in the distribution                                                                                                      
###   of rain frequency and intensity in response to global warming.                                                                                                            
###   Journal of Climate, 27, 8372-8383. doi:10.1175/JCLI-D-14-00183.1.                                                                                                         
###
### See github.com/apendergrass for the latest info and updates. 
##########################################################################
import os
import sys
#from netCDF4 import Dataset
import numpy as np
#import matplotlib.pyplot as plt

import time, json

import cdms2, cdtime
import MV2
import pcmdi_metrics
import cdutil
import collections

import datetime
year = datetime.date.today().year
month = datetime.date.today().month
day = datetime.date.today().day
#results_dir = "results_{}-{}-{}".format(year, month, day)

version = datetime.datetime.now().strftime('v%Y%m%d')


alib = 'a_pendergrass_rainmetrics_lib.py'

with open(alib) as source_file:
    exec(source_file.read())


L=2.5e6 # % w/m2. latent heat of vaporization of water
wm2tommd=1./L*3600*24 # % conversion from w/m2 to mm/d
#wm2tommd=1.  # PJG 

##### Load up the demo data. 
### It is daily average precipitation, in units of mm/d, with dimensions of lats, lons, and time. 
### We'll just use the first time period here, but there are two, and also the change in global mean surface temperature. 

run = 'c'
#run = 'a'

exp = 'historical'
#exp = 'amip'

#pathin = '/work/gleckler1/processed_data/daily_pr_apendergrass/cmip5/historical/'
#file1='pdistdemodata.nc'
#file1 = 'cmip5-test.nc'

test_run = 'n'  
regrid = 'y'

obs = 'n'
obs = 'y'
obs = 'GPCP'
#obs = 'CMORPH'
obs = 'TRMM'

sy = 1996
sm = 1
sd = 1
ey = 2005  #1998  #2005  #1982
em = 12
ed = 31

if obs == 'GPCP':
 sy = 1998
 sy = 2005
 ey = 2010

if obs == 'CMORPH':
 sy = 1998
 sy = 2003
 ey = 2013

if obs == 'TRMM':
 sy = 1998
 sy = 2003
 ey = 2010


months = [0,1,2,3,4,5,6,7,8,9,10,11,12]    #  0 = ALL TIMES, 1 = Jan, 12 = dec

#months = [2,3,4,5,6]

domain = 'GLOBAL'
#domain = '90S30S'
#domain = '30S30N'
#domain = '30N90N'
#domain = 'TROPICS'
domain = 'test_run'

domains = ['test_run','test_run1']
domains = ['GLOBAL','90S30S','30S30N','30N90N','50S30S','30N50N']

if obs == 'TRMM': domains = ['30S30N','50S30S','30N50N']

dom_dic = {}
dom_dic['GLOBAL']={}
dom_dic['TROPICS']={}
dom_dic['90S30S']= {}
dom_dic['30S30N']= {}
dom_dic['30N90N']= {}
dom_dic['50S30S']= {}
dom_dic['30N50N']= {}

dom_dic['test_run']={}
dom_dic['test_run1']={}
# 90/30/30/90  50/30/30/50

dom_dic['GLOBAL']['llat'] =-90.
dom_dic['GLOBAL']['ulat'] =90.

dom_dic['90S30S']['llat'] =-90.
dom_dic['90S30S']['ulat'] =-30.

dom_dic['30S30N']['llat'] =-30.
dom_dic['30S30N']['ulat'] = 30.

dom_dic['30N90N']['llat'] = 30.
dom_dic['30N90N']['ulat'] = 90.

dom_dic['50S30S']['llat'] = -50.
dom_dic['50S30S']['ulat'] = -30.

dom_dic['30N50N']['llat'] =  30.
dom_dic['30N50N']['ulat'] =  50.        
        
dom_dic['TROPICS']['llat'] =-30.
dom_dic['TROPICS']['ulat'] =30.
dom_dic['test_run']['llat'] =-5.
dom_dic['test_run']['ulat'] =5.
dom_dic['test_run1']['llat'] =5.
dom_dic['test_run1']['ulat'] =15.

io = 'netcdf4'
io = 'cdms2'

#pathin = '/work/cmip5-test/new/' + exp + '/atmos/day/pr/'
pathin = '/work/cmip-dyn/CMIP5/CMIP/' + exp + '/atmos/day/pr/'

outdir = '/p/user_pub/pmp/pmp_results/tree_v0.3/pmp_v1.1.2/metrics_results/pr/pr_dist_apendergrass/' + version + '/'

diags_outdir = '/export_backup/gleckler1/processing/metrics_package/my_test/angie_pr_dist/diagnostics/'
diags_outdir = '/p/user_pub/pmp/pmp_results/tree_v0.3/pmp_v1.1.2/diagnostic_results/pr/pr_dist_apendergrass/' + version + '/'

for dd in [outdir,diags_outdir]:
  try:
   os.mkdir(dd)
  except:
   pass

if regrid == 'y':
  regrid_tool  = 'regrid2' #'esmf'
  regrid_method = 'regrid2' #'conservative'
  regrid_dim = '2.5x2.5'
#  regrid_dim = '1x1'

#obs = 'n'
#obs = 'y'
#obs = 'GPCP'
#obs = 'CMORPH'


if obs == 'GPCP': 
  pathin = '/p/user_pub/pmp/pmp_results/tree_v0.3/pmp_v1.1.2/data/PMPObs/PMPObs_v1.3/atmos/day/pr/GPCP-1-3/gn/v20180816/'
if obs == 'CMORPH':
  pathin = '/p/user_pub/pmp/pmp_obs/orig/data/CMORPH_V1.0_NCAR/gpfs/fs1/p/cgd/cas/zhangyx/CMORPH_v1.0/0.25deg-HOURLY/CMORPH1.0_daily_2.5x2.5/'

if obs == 'TRMM':
  pathin = '/export_backup/gleckler1/processing/metrics_package/my_test/angie_pr_dist/a_TRMM/'

###########

lstt = os.listdir(pathin)

if obs == 'CMORPH': lstt = ['CMORPH_v1.0_all.xml']
#if obs == 'TRMM': lstt = ['TRMM_3B42_daily.2003.7.nc','TRMM_3B42_daily.2004.7.nc', 'TRMM_3B42_daily.2005.7.nc','TRMM_3B42_daily.2006.7.nc','TRMM_3B42_daily.2007.7.nc','TRMM_3B42_daily.2008.7.nc','TRMM_3B42_daily.2009.7.nc','TRMM_3B42_daily.2010.7.nc']

if obs == 'TRMM': lstt = ['TRMM_2003-2010.xml']

lst = []
for l in lstt:
  if l.find('MIROC4h') == -1 and l.find('MRI-AGCM3-2S') == -1: lst.append(l)

print('Complete list of files is: ', lst)
#print('DOMAIN IS ', domain)
#print "lst0 is ", lst[0]


if regrid == 'y':
 foc = '/work/gleckler1/processed_data/obs/atm/mo/pr/GPCP/ac/pr_GPCP_000001-000012_ac.nc'
 if regrid_dim == '2.5x2.5':
   foc = '/p/user_pub/pmp/pmp_obs/obs/atm/mo/pr/GPCP/ac/pr_GPCP_000001-000012_ac.nc' 
   fo = cdms2.open(foc)
   do = fo('pr')
   fo.close()
 if regrid_dim == '1x1':
   foc = '/p/user_pub/pmp/pmp_obs/obs/atm/mo/rlut/CERES/ac/rlut_CERES_000001-000012_ac.nc'
   fo = cdms2.open(foc)
   do = fo('rlut')
   fo.close()
 #print('OBS READ')

#if test_run == 'y': 
 obs_grids_dic = {}
 for dom in ['GLOBAL','90S30S','30S30N','30N90N','50S30S','30N50N']:
  dot = do(latitude = (dom_dic[dom]['llat'],dom_dic[dom]['ulat']))  #,longitude = (-10.,10.))
  obs_grid = dot.getGrid()
  obs_grids_dic[dom] = obs_grid

def getDailyCalendarMonth(d,mi):
 import MV2
 a = d.getTime()
 a.designateTime()
 cdutil.setTimeBoundsDaily(a)
 print(d.shape)

 if mi == 0: mot = 'jan'
 if mi == 1: mot = 'feb' 
 if mi == 2: mot = 'mar'
 if mi == 3: mot = 'apr'
 if mi == 4: mot = 'may'
 if mi == 5: mot = 'jun'
 if mi == 6: mot = 'jul'
 if mi == 7: mot = 'aug'
 if mi == 8: mot = 'sep'
 if mi == 9: mot = 'oct'
 if mi == 10: mot = 'nov'
 if mi == 11: mot = 'dec'
 
 indices, bounds, starts = cdutil.monthBasedSlicer(a, [mot,])

 calmo = None
 b = MV2.ones(a.shape)
 b.setAxis(0,a)

 for i, sub in enumerate(indices):
    tmp = d(time=slice(sub[0],sub[-1]+1))
#    print("Year",i,"shape of ",mot,tmp.shape)
    if calmo is None:
        calmo = tmp
    else:
        calmo = MV2.concatenate((calmo, tmp),axis=2)
 return calmo

#dic_tmp = {}
#for l in lst[7:8]:
#### LOOP THROUGH ALL IN MODLIST #################
##################################################
for l in lst:   #[0:2]:
#try:
  a = time.time()
  l = pathin + l
# print 'full path is -----', l
#print l.split('/')
  if obs == 'n':
   tmp = l.split('/')[9]
   print('tmp is ', tmp)
   mod = tmp.split('.')[4] 
   rip = tmp.split('.')[5]

  if obs == 'GPCP':
   tmp = l.split('/')[9]
   print('tmp is ', tmp)
   mod = 'GPCP-1-3' 
   rip = 'BE' 

  if obs == 'CMORPH':
#  tmp = l.split('/')[9]
#  print('tmp is ', tmp)
   mod = 'CMORPH-1-0'
   rip = 'BE'

  if obs == 'TRMM':
#  tmp = l.split('/')[9]
#  print('tmp is ', tmp)
   mod = 'TRMM-3B'
   rip = 'BE'

  dic_tmp = {} 
#  if mod not in dic_tmp.keys(): 
  dic_tmp[mod] = {}
  dic_tmp[mod][rip]= {}

#### LOOP THROUGH DOMAINS FOR EACH MODLIST ENTRY
##################################################
  
  for domain in domains:
   print('--------------------- ')
   print(mod, rip,' ',domain)


   if regrid != 'y':
         g = cdms2.open(diags_outdir + mod + '_' + rip + '_' + exp + '_' + domain + '.nc','w+')
   if regrid == 'y':
         g = cdms2.open(diags_outdir + mod + '_' + rip + '_' + exp + '_' + domain + '_' + regrid_tool + '_' + regrid_method + '_' + regrid_dim +  '.nc','w+')

   json_filename = 'apenderass_metrics_cmip5-' + exp + '_' + mod + '_' + rip + '_' + str(sy) +'.'+ str(sm) + '.' + str(sd) + '-' + str(ey) + '.' + str(em) + '.' + str(ed) + '_' + regrid_tool + '_' + regrid_method + '_' + regrid_dim + '.json'
   if regrid != 'y': json_filename = 'apenderass_metrics_cmip5-' + exp + '_' + mod + '_' + rip + '_' + str(sy) +'.'+ str(sm) + '.' + str(sd) + '-' + str(ey) + '.' + str(em) + '.' + str(ed) + '.json'

   if test_run == 'y': json_filename = json_filename.replace('.json','_test.json')

   if obs == 'y': json_filename = json_filename.replace('cmip5','obs')

   print('AFTER outputfiles defined')

#print 'MOD AND RIP ARE ----------------- ', mod, rip

#   if io == 'netcdf4':
#    fh = Dataset(pathin + file1, mode='r')
#   pdata1 = fh.variables['pr'][0:3650]   # PJG
#   lats_ax = fh.variables['lat']
#   lons_ax = fh.variables['lon']
#   lat = lats_ax[:]
#   lon = lons_ax[:]

   if io == 'cdms2':
# print "USING CDMS..."
    fh = cdms2.open(l)
# fh = cdms2.open(pathin + file, mode='r')
#   if test_run != 'y': pdata = fh('pr',time = (cdtime.comptime(sy,sm,sd),cdtime.comptime(ey,em,ed)))
#   if test_run == 'y': pdata = fh('pr',time = (cdtime.comptime(sy,sm,sd),cdtime.comptime(ey,em,ed)),latitude = (-5.,5.),longitude = (-10.,10.))
    pdata = fh('pr',time = (cdtime.comptime(sy,sm,sd),cdtime.comptime(ey,em,ed)),latitude = (dom_dic[domain]['llat'],dom_dic[domain]['ulat']))

    print('DATA READ!')
    if obs == 'TRMM': pdata = MV2.divide(pdata,86400.)

#var = var.regrid(self.target_grid, regridTool=self.regrid_tool, regridMethod=self.regrid_method, coordSys='deg', diag={}, periodicity=1)
    if regrid == 'y':
       a1 = time.time()
       pdata = pdata.regrid(obs_grids_dic[domain],regridTool=regrid_tool,regridMethod=regrid_method)
       a2 = time.time()
       print('time to regrid ', a2-a1)

    print(pdata.shape)
# pdata = fh('pr',time = slice(0,730))

    pdata = MV2.transpose(pdata)

    lat = pdata.getLatitude()[:]
    lon = pdata.getLongitude()[:]
    lats_ax = pdata.getLatitude() 
    lons_ax = pdata.getLongitude() 

    pdata_all = pdata*1.

#    pdata1_all = pdata.filled() 
 #  pdata1_all = pdata1*86400.

#  print '--------------------- '
#  print mod, rip,' ', pdata1.shape

   fh.close()
   
   b = time.time()

   print('time reading data --- ', b-a)

   cdutil.setTimeBoundsDaily(pdata_all,1)
   dic_tmp[mod][rip][domain] = {}   

   amtpeakmap_mo=np.empty((len(lon),len(lat),12))
   amtwidthmap_mo=np.empty((len(lon),len(lat),12))
   pdfpeakmap_mo=np.empty((len(lon),len(lat),12))
   pdfwidthmap_mo=np.empty((len(lon),len(lat),12))
   amtpeakzm_mo=np.empty((len(lat),12))
   amtwidthzm_mo=np.empty((len(lat),12))
   pdfpeakzm_mo=np.empty((len(lat),12))
   pdfwidthzm_mo=np.empty((len(lat),12))

   for mo in months:
       
       if mo == 0: 
           pdata1 = pdata_all
           mo_txt = 'ALL'
       if mo == 1: 
           pdata1 = getDailyCalendarMonth(pdata_all,0) 
           mo_txt = 'JAN'
       if mo == 2: 
           pdata1 = getDailyCalendarMonth(pdata_all,1) 
           mo_txt = 'FEB'
       if mo == 3: 
           pdata1 = getDailyCalendarMonth(pdata_all,2) 
           mo_txt = 'MAR'
       if mo == 4: 
           pdata1 = getDailyCalendarMonth(pdata_all,3) 
           mo_txt = 'APR'
       if mo == 5: 
           pdata1 = getDailyCalendarMonth(pdata_all,4) 
           mo_txt = 'MAY'
       if mo == 6: 
           pdata1 = getDailyCalendarMonth(pdata_all,5) 
           mo_txt = 'JUN'          
       if mo == 7: 
           pdata1 = getDailyCalendarMonth(pdata_all,6) 
           mo_txt = 'JUL'
       if mo == 8: 
           pdata1 = getDailyCalendarMonth(pdata_all,7) 
           mo_txt = 'AUG'
       if mo == 9: 
           pdata1 = getDailyCalendarMonth(pdata_all,8) 
           mo_txt = 'SEP'
       if mo == 10: 
           pdata1 = getDailyCalendarMonth(pdata_all,9) 
           mo_txt = 'OCT'
       if mo == 11: 
           pdata1 = getDailyCalendarMonth(pdata_all,10) 
           mo_txt = 'NOV'
       if mo == 12: 
           pdata1 = getDailyCalendarMonth(pdata_all,11) 
           mo_txt = 'DEC'          

#       dic_tmp[mod][rip][domain] = {}
       dic_tmp[mod][rip][domain][mo_txt] = {}

#       print "working on ", mod,' ',rip,' ', mo_txt,' ', domain
#       print 'pdata1 shape and type ', pdata1.shape,' ', type(pdata1)
       
       pdata1 = pdata1.filled() 
       pdata1 = pdata1*86400.   
       
        #### 1. Calculate bin structure. Note, these were chosen based on daily CMIP5 data - if you're doing something else you might want to change it
       sp1=pdata1.shape
       if (sp1[1]!=len(lat))&(sp1[0]!=len(lon)):
          print('pdata1 should be [days,lat,lon]')
       pmax=pdata1.max()/wm2tommd
       maxp=1500;# % choose an arbitrary upper bound for initial distribution, in w/m2
       minp=1;# % arbitrary lower bound, in w/m2. Make sure to set this low enough that you catch most of the rain. 
        #%%% thoughts: it might be better to specify the minimum threshold and the                                     
        #%%% bin spacing, which I have around 7%. The goals are to capture as much                                     
        #%%% of the distribution as possible and to balance sampling against                                           
        #%%% resolution. Capturing the upper end is easy: just extend the bins to                                      
        #%%% include the heaviest precipitation event in the dataset. The lower end                                    
        #%%% is harder: it can go all the way to machine epsilon, and there is no                                       
        #%%% obvious reasonable threshold for "rain" over a large spatial scale. The                                   
        #%%% value I chose here captures 97% of rainfall in CMIP5.                                                     
       nbins=100;
       binrlog=np.linspace(np.log(minp),np.log(maxp),nbins);
       dbinlog=np.diff(binrlog);
       binllog=binrlog-dbinlog[0];
       binr=np.exp(binrlog)/L*3600*24;
       binl=np.exp(binllog)/L*3600*24;
       dbin=dbinlog[0];
       binrlogex=binrlog;
       binrend=np.exp(binrlogex[len(binrlogex)-1])
        #% extend the bins until the maximum precip anywhere in the dataset falls
        #% within the bins
        # switch maxp to pmax if you want it to depend on your data
       while maxp>binr[len(binr)-1]:
          binrlogex=np.append(binrlogex,binrlogex[len(binrlogex)-1]+dbin)
          binrend=np.exp(binrlogex[len(binrlogex)-1]);
          binrlog=binrlogex;
          binllog=binrlog-dbinlog[0];
          binl=np.exp(binllog)/L*3600*24; #%% this is what we'll use to make distributions
          binr=np.exp(binrlog)/L*3600*24;
       bincrates=np.append(0,(binl+binr)/2)# % we'll use this for plotting.
        #### 2. Calculate distributions 
    
       ppdfmap,pamtmap=makedists(pdata1,binl);
## PJG ADDING ZONAL MEAN       
       ppdfzm=np.nanmean(ppdfmap,axis=0)    
       pamtzm=np.nanmean(pamtmap,axis=0)   

       amtpeakzm=np.empty(len(lat))
       pdfpeakzm=np.empty(len(lat))
       amtwidthzm=np.empty(len(lat))
       pdfwidthzm=np.empty(len(lat))
       for j in range(len(lat)):
              rainpeak,rainwidth,plotpeak,plotwidth=calcrainmetrics(pamtzm[j,:],bincrates)
              amtpeakzm[j]=rainpeak
              amtwidthzm[j]=rainwidth
              rainpeak,rainwidth,plotpeak,plotwidth=calcrainmetrics(ppdfzm[j,:],bincrates)
              pdfpeakzm[j]=rainpeak
              pdfwidthzm[j]=rainwidth

       if mo != 0:
        amtpeakzm_mo[:,mo-1] = amtpeakzm
        pdfpeakzm_mo[:,mo-1] = pdfpeakzm
        amtwidthzm_mo[:,mo-1] = amtwidthzm
        pdfwidthzm_mo[:,mo-1] = pdfwidthzm

#      dic_tmp[mod][rip][domain][mo_txt]['rain_amount-zm'] = {}
#      dic_tmp[mod][rip][domain][mo_txt]['rain_frequency-zm'] = {}
#      dic_tmp[mod][rip][domain][mo_txt]['rain_amount-zm']['peak'] = rainamtpeakzm
#      dic_tmp[mod][rip][domain][mo_txt]['rain_amount-zm']['width'] = rainamtwidthzm
#      dic_tmp[mod][rip][domain][mo_txt]['rain_frequency-zm']['rainpdfpeak'] = rainpdfpeakzm
#      dic_tmp[mod][rip][domain][mo_txt]['rain_frequency-zm']['rainpdfwidth'] = rainpdfwidthzm

## END PJG ADD ZONAL MEANS

        #### 3. Spatially average distributions
       weight=np.tile(np.cos(lat*np.pi/180),(len(lon),1));
       weight=weight/weight.sum()
       weightp=np.tile(np.expand_dims(weight,axis=2),(1,1,ppdfmap.shape[2]))
    
#       print weightp.shape, ' ', ppdfmap.shape
       ppdf1=np.nansum(np.nansum(ppdfmap*weightp,axis=0),axis=0)
       pamt1=np.nansum(np.nansum(pamtmap*weightp,axis=0),axis=0)
    
    #w = sys.stdin.readline()
#       c = time.time()
#       print 'calculating bin structure --- ', c-b 
     
    #### Calculate the rain metrics for the averaged distribution
    #print 'calculate rain metrics for average distribution'
    
    
       rainamtpeak,rainamtwidth,plotpeakamt,plotwidthamt=calcrainmetrics(pamt1,bincrates)
       rainpdfpeak,rainpdfwidth,plotpeakfreq,plotwidthfreq=calcrainmetrics(ppdf1,bincrates)
    ### Print the metrics for the averaged distribution
    #print "rain amount of average distribution"
    #print '  peak: '+"{:.1f}".format(rainamtpeak)+' mm/d'
    #print '  width: '+"{:.1f}".format(rainamtwidth)+' r2/r1'
    #print "rain frequency of average distribution"
    #print '  peak: '+"{:.1f}".format(rainpdfpeak)+' mm/d'
    #print '  width: '+"{:.1f}".format(rainpdfwidth)+' r2/r1'
    
       dic_tmp[mod][rip][domain][mo_txt]['rain_amount'] = {}
       dic_tmp[mod][rip][domain][mo_txt]['rain_frequency'] = {}
       dic_tmp[mod][rip][domain][mo_txt]['rain_amount']['peak'] = rainamtpeak
       dic_tmp[mod][rip][domain][mo_txt]['rain_amount']['width'] = rainamtwidth
       dic_tmp[mod][rip][domain][mo_txt]['rain_frequency']['rainpdfpeak'] = rainpdfpeak
       dic_tmp[mod][rip][domain][mo_txt]['rain_frequency']['rainpdfwidth'] = rainpdfwidth
    
######
  
    ### now we'll make maps of the metrics to examine their spatial pattern. 
    
    ### Calculate the metrics for the distribution at each grid point
    # ppdfmap,pamtmap=makedists(pdata1,binl);
       bincrates = bincrates[0:len(bincrates)-1]  ### PJG ADDED LINE HERE    
       amtpeakmap=np.empty((len(lon),len(lat)))
       pdfpeakmap=np.empty((len(lon),len(lat)))
       amtwidthmap=np.empty((len(lon),len(lat)))
       pdfwidthmap=np.empty((len(lon),len(lat)))
       for i in range(len(lon)):
          for j in range(len(lat)):
              rainpeak,rainwidth,plotpeak,plotwidth=calcrainmetrics(pamtmap[i,j,:],bincrates)
              amtpeakmap[i,j]=rainpeak
              amtwidthmap[i,j]=rainwidth
              rainpeak,rainwidth,plotpeak,plotwidth=calcrainmetrics(ppdfmap[i,j,:],bincrates)
              pdfpeakmap[i,j]=rainpeak
              pdfwidthmap[i,j]=rainwidth

       if mo != 0:
        amtpeakmap_mo[:,:,mo-1] = amtpeakmap
        pdfpeakmap_mo[:,:,mo-1] = pdfpeakmap
        amtwidthmap_mo[:,:,mo-1] = amtwidthmap
        pdfwidthmap_mo[:,:,mo-1] = pdfwidthmap
    
#       print 'made it to A'
    
       if mo_txt == 'ALL':
        dset = -1
        for calc in [amtpeakmap, amtwidthmap, pdfpeakmap, pdfwidthmap,amtpeakzm, amtwidthzm, pdfpeakzm, pdfwidthzm]:   
         dset = dset + 1
         d = cdms2.createVariable(calc)
         if dset in [0,1,2,3]:
          d.setAxis(0,lons_ax) 
          d.setAxis(1,lats_ax)
         if dset in [4,5,6,7]:
          d.setAxis(0,lats_ax)
         d = MV2.transpose(d)
         if dset == 0: d.id = 'amtpeakmap_' + mo_txt 
         if dset == 1: d.id = 'amtwidthmap_' + mo_txt
         if dset == 2: d.id = 'pdfpeakmap_' + mo_txt
         if dset == 3: d.id = 'pdfwidthmap_' + mo_txt
         if dset == 4: d.id = 'amtpeakzm_' + mo_txt
         if dset == 5: d.id = 'amtwidthzm_' + mo_txt
         if dset == 6: d.id = 'pdfpeakzm_' + mo_txt
         if dset == 7: d.id = 'pdfwidthzm_' + mo_txt
         g.write(d)

    
    # =================================================
    # Write dictionary to json file
    # (let the json keep overwritten in model loop)
    # -------------------------------------------------
    
       OUT = pcmdi_metrics.io.base.Base(os.path.abspath(outdir), json_filename)
       metrics_dictionary = collections.OrderedDict()
       metrics_def_dictionary = collections.OrderedDict()
    #  metrics_dictionary["DISCLAIMER"] = 'crap'  #disclaimer
       metrics_dictionary["REFERENCE"] = "The statistics in this file are based on Pendergrass, A. G., and C. Deser, 2017: Climatological characteristics of typical daily precipitation. Journal of Climate, 30, 5985-6003, doi:10.1175/JCLI-D-16-0684.1.  The analysis code used to produce these results is maintained at https://github.com/apendergrass/rain-metrics-python, which has been integrated into the PMP (https://github.com/PCMDI/pcmdi_metrics) to produce the results below."
    
       metrics_dictionary["RESULTS"] = dic_tmp # collections.OrderedDict()
    
       OUT.var = 'pr' 
       OUT.write(
        metrics_dictionary,
        json_structure=["model", "realization", "domain","month","statistic"],
        indent=4,
        separators=(
            ',', ': '))

## END OF LOOPING OVER MONTHS
#  if mo_txt != 'ALL':
   dset = -1
   t_ax = cdms2.createAxis([1,2,3,4,5,6,7,8,9,10,11,12],id = 'month')
   for calc in [amtpeakmap_mo, amtwidthmap_mo, pdfpeakmap_mo, pdfwidthmap_mo,amtpeakzm_mo, amtwidthzm_mo, pdfpeakzm_mo, pdfwidthzm_mo]:
         dset = dset + 1
         d = cdms2.createVariable(calc)
         if dset in [0,1,2,3]:
          d.setAxis(0,lons_ax)
          d.setAxis(1,lats_ax)
          d.setAxis(2,t_ax)
         if dset in [4,5,6,7]:
          d.setAxis(0,lats_ax)
          d.setAxis(1,t_ax)
         d = MV2.transpose(d)

         if dset == 0: d.id = 'amtpeakmap' 
         if dset == 1: d.id = 'amtwidthmap' 
         if dset == 2: d.id = 'pdfpeakmap' 
         if dset == 3: d.id = 'pdfwidthmap' 
         if dset == 4: d.id = 'amtpeakzm' 
         if dset == 5: d.id = 'amtwidthzm' 
         if dset == 6: d.id = 'pdfpeakzm' 
         if dset == 7: d.id = 'pdfwidthzm' 
         g.write(d)
   g.close()

#except:
#  print('FAILED WITH ------ ', mod,' ', rip)

