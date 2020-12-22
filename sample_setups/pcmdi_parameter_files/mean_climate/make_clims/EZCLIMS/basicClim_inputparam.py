import datetime

ver = datetime.datetime.now().strftime('v%Y%m%d') #PCMDI versioning

mip = 'cmip6'
exp = 'historical'  # historical or amip
latest_xmls = 'v20191126'
start = '1981-01'
end = '2006-01'

start_month = 1
start_year = 1981
end_month = 1
end_year = 2006


modpath = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/' + latest_xmls + '/' + mip + '/' + exp + '/atmos/mon/VARIABLE/'

filename_template = mip + '.' + exp + '.MODEL.mon.VARIABLE.xml'

model = ['GFDL-CM4.r1i1p1f1','GFDL-ESM4.r1i1p1f1']
#model = ['UKESM1-0-LL.r1i1p1f2']

variable = ['rlut']

print('mods are ', model)

output_filename_template = 'MODEL.mon.VARIABLE.' +  start.replace('-','') + '-' + end.replace('-','') + '.AC.' + ver + '.nc'

results_dir = './simple_test/'

