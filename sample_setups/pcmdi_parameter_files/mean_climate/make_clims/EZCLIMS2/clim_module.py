def clim_calc(var, infile,outfile,outdir,outfilename,start,end):
   import cdms2
   import cdutil
   import cdtime 
   import datetime
   import os

   ver = datetime.datetime.now().strftime('v%Y%m%d') 

   l = infile
   tmp = l.split('/')
   infilename = tmp[len(tmp)-1]

   print('infilename is ', infilename)

   f = cdms2.open(l)
   atts = f.listglobal()
   outfd = outfile


### CONTROL OF OUTPUT DIRECTORY AND FILE

## outdir AND outfilename PROVIDED BY USER
   if outdir is not None and outfilename is not None: outfd = outdir + outfilename

## outdir PROVIDED BY USER, BUT filename IS TAKEN FROM infilename WITH CLIM MODIFICATIONS SUFFIX ADDED BELOW
   if outdir is not None and outfilename is None: outfd = outdir + infilename

   if outdir is None and outfilename is None:    # WORKING!!!
        outfd = outfile
        
   print('outfd is ', outfd)
   print('outdir is ', outdir)

######


   seperate_clims = 'y'

### DEFAULT CLIM - BASED ON ENTIRE TIME SERIES
   if start == end == None: 
    d = f(var) 
    t = d.getTime()
    c = t.asComponentTime()
    start_yr_str = str(c[0].year)
    start_mo_str = str(c[0].month)
    end_yr_str = str(c[len(c)-1].year)
    end_mo_str = str(c[len(c)-1].month)
    start_yr_int = int(c[0].year)
    start_mo_int = int(c[0].month)
    end_yr_int = int(c[len(c)-1].year)
    end_mo_int = int(c[len(c)-1].month)
### USER DEFINED PERIOD
   else:
    start_mo = int(start.split('-')[1])
    start_yr = int(start.split('-')[0])
    end_mo = int(end.split('-')[1])
    end_yr = int(end.split('-')[0])
    start_yr_str = str(start_yr)
    start_mo_str = str(start_mo)
    end_yr_str = str(end_yr)
    end_mo_str = str(end_mo)
    d = f(var,time=(cdtime.comptime(start_yr,start_mo),cdtime.comptime(end_yr,end_mo)))

   print("start_yr_str is ", start_yr_str)

   if start_mo_str not in ['11','12']: start_mo_str = '0' + start_mo_str
   if end_mo_str not in ['11','12']: end_mo_str = '0' + end_mo_str

   d_ac =   cdutil.ANNUALCYCLE.climatology(d).astype('Float32')
   d_djf =  cdutil.DJF.climatology(d)(squeeze=1).astype('Float32')
   d_jja =  cdutil.JJA.climatology(d)(squeeze=1).astype('Float32')
   d_son =  cdutil.SON.climatology(d)(squeeze=1).astype('Float32')
   d_mam =  cdutil.MAM.climatology(d)(squeeze=1).astype('Float32')

   for v in [d_ac,d_djf,d_jja,d_son,d_mam]:
     v.id = var
#    v.time_series_produced = ts_date  #ts_date_linkvalue  #ts_date

   for s in ['AC','DJF','MAM','JJA','SON']:

    addf = '.' + start_yr_str + start_mo_str + '-' + end_yr_str + end_mo_str + '.' + s + '.' + ver + '.nc'
#   if seperate_clims == 'y': 
    print('outfd is ', outfd)
    out = outfd
    out = out.replace('.xml',addf)
    out = out.replace('.nc',addf)
    print('out is ', out)

    if seperate_clims == 'n':  out = outfd.replace('climo.nc',s+'.nc')
    if s == 'AC': do = d_ac
    if s == 'DJF': do = d_djf
    if s == 'MAM': do = d_mam
    if s == 'JJA': do = d_jja
    if s == 'SON': do = d_son
    do.id = var

### MKDIRS AS NEEDED
#   print(outdir)
#   print(outdir.split('/'))
    lst = outfd.split('/')
    s = '/'
    for l in range(len(lst)):
     d = s.join(lst[0:l])
     print(d)
     try:
      os.mkdir(d)
     except:
      pass
  
    g = cdms2.open(out,'w+')
    g.write(do)

    for att in atts:
     setattr(g,att,f.getglobal(att))
    g.close()
    print(do.shape,' ', d_ac.shape,' ',out)
   f.close()

