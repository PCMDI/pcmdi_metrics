import glob

var = 'rlut'
ver = 'v20201226' 
pin = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/' + ver + '/cmip6/historical/atmos/mon/' + var + '/'

lst = glob.glob(pin + '*r1i1p1f1*.xml')

cmd0 = "python ./clim_calc_driver.py -p clim_calc_cmip_inparam.py --start 1979-01 --end 1989-12 --infile "

for l in lst:
  print(cmd0 + l)
  
