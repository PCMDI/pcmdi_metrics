import datetime
import glob
import os

from pcmdi_metrics.misc.scripts import parallel_submitter

exp = 'historical'
# exp = 'amip'
mip = 'cmip6'
verin = 'v20230201'  #'v20210731'  #'v20201226'
start = '1981-01'
end = '2005-12'
numw = 35  # None   #35
verout = datetime.datetime.now().strftime('v%Y%m%d')

# vars = ['rlut', 'tas', 'pr']
# vars = ['ts', 'tas', 'uas', 'vas', 'huss', 'hurs', 'psl', 'prw', 'sfcWind', 'tauu', 'tauv', 'pr', 'rlut', 'rsut', 'rlutcs', 'rsutcs', 'rsdt', 'rsus', 'rsds', 'rlds', 'rlus', 'rldscs', 'rsdscs']
# vars = ['ta', 'ua', 'va', 'zg', 'hur', 'hus']
# vars = ['ts', 'tas', 'uas', 'vas', 'huss', 'hurs', 'psl', 'prw', 'sfcWind', 'tauu', 'tauv', 'pr', 'rlut', 'rsut', 'rlutcs', 'rsutcs', 'rsdt', 'rsus', 'rsds', 'rlds', 'rlus', 'rldscs', 'rsdscs', 'ta', 'ua', 'va', 'zg', 'hur', 'hus']
vars = ['ts', 'pr']

lst1 = []
listlog = []

for var in vars:
    pin = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/additional_xmls/latest/' + verin + '/' + mip + '/' + exp + '/atmos/mon/' + var + '/'

    lst = sorted(glob.glob(pin + '*r1i1p1f1*.xml'))

    pathout_base = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/CMIP_CLIMS/' + mip + '/' + exp + '/'
    pathoutdir = os.path.join(pathout_base, verout, var)

    os.makedirs(pathoutdir, exist_ok=True)

    for li in lst:

        print(li.split('.'))
        mod = li.split('.')[4]
        rn = li.split('.')[5]
        vv = li.split('.')[7]

        outfilename = mip + '.' + exp + '.' + mod + '.r1i1p1f1.mon.' + var + '.nc'
        cmd0 = "pcmdi_compute_climatologies.py --start " + start + " --end " + end + " --infile "

        pathout = pathoutdir + '/' + outfilename
        cmd = cmd0 + li + ' --outfile ' + pathout + ' --var ' + var

        lst1.append(cmd)
        logf = mod + '.' + rn + '.' + vv + '.txt'
        listlog.append(logf)
        print(logf)

print('Number of jobs starting is ', str(len(lst1)))
parallel_submitter(lst1, log_dir='./logs', logfilename_list=listlog, num_workers=numw)
print('done submitting')
