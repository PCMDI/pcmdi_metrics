import cdms2
import glob
import MV2
import os

from plot_wavenumber_frequency_power import plot_power
from lib_mjo import calculate_ewr


def main():
    mip = 'cmip5'
    # mip = 'cmip6'
    exp = 'historical'
    version = 'v20200807'
    period = '1985-2004'
    datadir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/mjo/'+mip+'/historical/'+version
    imgdir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/graphics/mjo/'+mip+'/historical/'+version
    seasons = ["NDJFMA", "MJJASO"]

    ncfile_list = glob.glob(os.path.join(datadir, '*.nc'))

    # get list of models
    models_list = sorted([r.split('/')[-1].split('.')[0].split('_')[1] for r in ncfile_list])
    # remove repeat
    models_list = list(dict.fromkeys(models_list))
    # remove obs
    models_list.remove('obs')

    # models_list = models_list[0:1]
    print(models_list)

    for season in seasons:
        for model in models_list:
            ncfile_list_model = glob.glob(os.path.join(datadir, '*_'+model+'_*_'+season+'_cmmGrid.nc'))
            runs_list = sorted([r.split('/')[-1].split('.')[0].split('_')[3] for r in ncfile_list_model])
            print(model, runs_list)
            d_runs = []
            for run in runs_list:
                try:
                    ncfile = '_'.join([mip, model, exp, run, 'mjo', period, season, 'cmmGrid'])+'.nc'
                    f = cdms2.open(os.path.join(datadir, ncfile))
                    d = f('power')
                    d_runs.append(d)
                    f.close()
                except Exception as err:
                    print(model, run, 'cannnot load:', err)
                    pass
                if run == runs_list[-1]:
                    num_runs = len(d_runs)
                    # ensemble mean
                    d_avg = MV2.average(d_runs, axis=0)
                    d_avg.setAxisList(d.getAxisList())
                    title = (mip.upper() + ': ' + model + ' (' + str(num_runs) +
                             ' runs mean) \n Pr, NDJFMA, ' + period + ', common grid (2.5x2.5deg)')
                    # E/W ratio
                    ewr, eastPower, westPower = calculate_ewr(d_avg)
                    # plot prepare
                    pngfilename = ncfile.split('.nc')[0].replace(run, 'average')
                    fout = os.path.join(imgdir, pngfilename)
                    # plot
                    plot_power(d_avg, title, fout, ewr)


if __name__ == "__main__":
    main()
