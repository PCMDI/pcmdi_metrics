def clim_calc(var, infile,outfile):
   import cdms2
   import cdutil
   l = infile
   f = cdms2.open(l)
   atts = f.listglobal()
   outfd = outfile

   seperate_clims = 'y'

   d = f(var) 
   t = d.getTime()
   c = t.asComponentTime()
   start_yr = str(c[0].year)
   start_mo = str(c[0].month)
   end_yr = str(c[len(c)-1].year)
   end_mo = str(c[len(c)-1].month)

   if start_mo not in ['11','12']: start_mo = '0' + start_mo
   if end_mo not in ['11','12']: end_mo = '0' + end_mo

   d_ac =   cdutil.ANNUALCYCLE.climatology(d).astype('Float32')
   d_djf =  cdutil.DJF.climatology(d)(squeeze=1).astype('Float32')
   d_jja =  cdutil.JJA.climatology(d)(squeeze=1).astype('Float32')
   d_son =  cdutil.SON.climatology(d)(squeeze=1).astype('Float32')
   d_mam =  cdutil.MAM.climatology(d)(squeeze=1).astype('Float32')

   for v in [d_ac,d_djf,d_jja,d_son,d_mam]:
     v.id = var
#    v.time_series_produced = ts_date  #ts_date_linkvalue  #ts_date

   for s in ['AC','DJF','MAM','JJA','SON']:

    addf = '.' + start_yr + start_mo + '-' + end_yr + end_mo + '.' + s + '.nc'
    if seperate_clims == 'y':  out = outfd.replace('.nc',addf)
    if seperate_clims == 'n':  out = outfd.replace('climo.nc',s+'.nc')
    if s == 'AC': do = d_ac
    if s == 'DJF': do = d_djf
    if s == 'MAM': do = d_mam
    if s == 'JJA': do = d_jja
    if s == 'SON': do = d_son
    do.id = var

    g = cdms2.open(out,'w+')
    g.write(do)

    for att in atts:
     setattr(g,att,f.getglobal(att))
    g.close()
    print(do.shape,' ', d_ac.shape,' ',out)
   f.close()

