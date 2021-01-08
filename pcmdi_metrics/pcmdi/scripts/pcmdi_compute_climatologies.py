import cdms2 
import datetime
import pcmdi_metrics

ver = datetime.datetime.now().strftime('v%Y%m%d')

cdms2.setNetcdfShuffleFlag(0)
cdms2.setNetcdfDeflateFlag(0)
cdms2.setNetcdfDeflateLevelFlag(0)

########


def clim_calc(var, infile, outfile, outdir, outfilename, start, end):
	import cdms2
    import cdutil
    import cdtime
    import datetime
    import os

    ver = datetime.datetime.now().strftime('v%Y%m%d')

    lf = infile
    tmp = lf.split('/')
    infilename = tmp[len(tmp)-1]
    print('infilename is ', infilename)

    f = cdms2.open(lf)
    atts = f.listglobal()
    outfd = outfile

# CONTROL OF OUTPUT DIRECTORY AND FILE

# outdir AND outfilename PROVIDED BY USER
    if outdir is not None and outfilename is not None: 
    	outfd = outdir + outfilename

# outdir PROVIDED BY USER, BUT filename IS TAKEN FROM infilename WITH CLIM MODIFICATIONS SUFFIX ADDED BELOW
    if outdir is not None and outfilename is None: 
    	outfd = outdir + '/' + infilename

    if outdir is None and outfilename is None:    # WORKING!!!
    	outfd = outfile

    print('outfd is ', outfd)
    print('outdir is ', outdir)

    seperate_clims = 'y'
	
# DEFAULT CLIM - BASED ON ENTIRE TIME SERIES
    if start == end is None:
    	d = f(var)
    	t = d.getTime()
    	c = t.asComponentTime()
    	start_yr_str = str(c[0].year)
    	start_mo_str = str(c[0].month)
    	end_yr_str = str(c[len(c)-1].year)
    	end_mo_str = str(c[len(c)-1].month)

# USER DEFINED PERIOD
    else:
     	start_mo = int(start.split('-')[1])
     	start_yr = int(start.split('-')[0])
     	end_mo = int(end.split('-')[1])
     	end_yr = int(end.split('-')[0])
     	start_yr_str = str(start_yr)
     	start_mo_str = str(start_mo)
     	end_yr_str = str(end_yr)
     	end_mo_str = str(end_mo)

    d = f(var, time=(cdtime.comptime(start_yr, start_mo), cdtime.comptime(end_yr, end_mo)))

    print("start_yr_str is ", start_yr_str)

    if start_mo_str not in ['11', '12']: 
    	start_mo_str = '0' + start_mo_str
    if end_mo_str not in ['11', '12']: 
      	end_mo_str = '0' + end_mo_str

    d_ac = cdutil.ANNUALCYCLE.climatology(d).astype('Float32')
    d_djf = cdutil.DJF.climatology(d)(squeeze=1).astype('Float32')
    d_jja = cdutil.JJA.climatology(d)(squeeze=1).astype('Float32')
    d_son = cdutil.SON.climatology(d)(squeeze=1).astype('Float32')
    d_mam = cdutil.MAM.climatology(d)(squeeze=1).astype('Float32')

    for v in [d_ac, d_djf, d_jja, d_son, d_mam]:
     	v.id = var

    for s in ['AC', 'DJF', 'MAM', 'JJA', 'SON']:

		addf = '.' + start_yr_str + start_mo_str + '-' + end_yr_str + end_mo_str + '.' + s + '.' + ver + '.nc'

#   if seperate_clims == 'y':
 
     	print('outfd is ', outfd)
     	out = outfd
     	out = out.replace('.xml', addf)
     	out = out.replace('.nc', addf)
     	print('out is ', out)

     if seperate_clims == 'n':  
     	out = outfd.replace('climo.nc', s+'.nc')
     if s == 'AC': 
     	do = d_ac
     if s == 'DJF': 
     	do = d_djf
     if s == 'MAM': 
     	do = d_mam
     if s == 'JJA': 
     	do = d_jja
     if s == 'SON': 
     	do = d_son
     do.id = var

### MKDIRS AS NEEDED
     lst = outfd.split('/')
     s = '/'
     for ll in range(len(lst)):
     	d = s.join(lst[0:ll])
      	try:
       		os.mkdir(d)
      	except:
       	pass

     g = cdms2.open(out, 'w+')
     g.write(do)
 
     for att in atts:
     	setattr(g,att,f.getglobal(att))
     g.close()
     	print(do.shape, ' ', d_ac.shape, ' ', out)
    f.close()

#######################################################################

P = pcmdi_metrics.driver.pmp_parser.PMPMetricsParser()

		
P.add_argument(
        '--var',
        dest='var',
        help='Defines var', 
        required=False)
P.add_argument(
        '--infile',
        dest='infile',
        help='Defines infile',  
        required=False)
P.add_argument(
        '--outfile',
        dest='outfile',
        help='Defines output path and filename',
        required=False)
P.add_argument(
        '--outpath',
        dest='outpath',
        help='Defines outpath only',
        required=False)
P.add_argument(
        '--outfilename',
        dest='outfilename',
        help='Defines out filename only',
        required=False)
P.add_argument(
        '--start',
        dest='start',
        help='Defines start year and month',
        required=False)
P.add_argument(
        '--end',
        dest='end',
        help='Defines end year and month',
        required=False)
			
args = P.get_parameter()

infile = args.infile
outfile = args.outfile
outpath = args.outpath
outfilename = args.outfilename
var = args.var
start = args.start
end = args.end

print('start and end are ', start, ' ', end)
print('var is ', var)

clim_calc(var, infile, outfile, outpath, outfilename, start, end)
#'''
#'''
