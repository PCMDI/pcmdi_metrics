import cdms2
import copy
import matplotlib.cm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import os


def plot_power(d, title, fout, ewr=None):

    y = d.getAxis(0)[:]
    x = d.getAxis(1)[:]

    # adjust font size
    SMALL_SIZE = 8
    MEDIUM_SIZE = 13
    BIGGER_SIZE = 15
    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=MEDIUM_SIZE)   # fontsize of the tick labels
    plt.rc('ytick', labelsize=MEDIUM_SIZE)   # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title

    # plot
    plt.switch_backend('agg')  # backend plotting
    plt.figure(figsize=(8, 4))
    cm = copy.copy(matplotlib.cm.get_cmap("jet"))
    cs = plt.contourf(
        x, y, d,
        levels=[0.002, 0.004, 0.006, 0.008, 0.01, 0.012, 0.014, 0.016,
                0.018, 0.020, 0.022, 0.024, 0.026, 0.028, 0.03, 0.032],
        cmap=cm,
        extend='both')
    cs.cmap.set_under('w')
    # y-axis range
    plt.ylim(0, 6)
    # eastward annotation
    plt.text(0.01, 5.5, 'Eastward', horizontalalignment='center', fontsize=12)
    plt.annotate('', xy=(0.001, 5.3), xycoords='data', xytext=(0.02, 5.3),
                 arrowprops=dict(arrowstyle="<|-", color='black', linewidth=3))
    # westward annotation
    plt.text(-0.01, 5.5, 'Westward', horizontalalignment='center', fontsize=12)
    plt.annotate('', xy=(-0.001, 5.3), xycoords='data', xytext=(-0.02, 5.3),
                 arrowprops=dict(arrowstyle="<|-", color='black', linewidth=3))
    # vertical line at 0 to distingush east and west
    plt.axvline(x=0, linestyle='dotted', color='black', linewidth=1)
    # east-west power ratio annotation
    if ewr is not None:
        plt.text(
            0.044, 5.5,
            'EWR = '+str(round(ewr, 2)),
            horizontalalignment='center',
            fontsize=12,
            bbox=dict(facecolor='white', alpha=0.5))
    currentAxis = plt.gca()
    currentAxis.add_patch(Rectangle((0.0166667, 1), 0.0333333-0.0166667, 2, edgecolor='black', ls='--', fill=None))
    currentAxis.add_patch(Rectangle((-0.0333333, 1), 0.0333333-0.0166667, 2, edgecolor='black', ls='--', fill=None))
    # title and labels
    plt.suptitle('Wavenumber-Frequency Power Spectra', fontsize=15)
    plt.title(title, y=1.015, fontsize=13)
    plt.xlabel('Frequency (cycles/day)')
    plt.ylabel('Wavenumber')
    # colorbar and margin adjust
    plt.colorbar()
    plt.subplots_adjust(left=0.08, right=1.04, top=0.8, bottom=0.13)
    # save
    plt.savefig(fout+'.png')


if __name__ == "__main__":

    datadir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/mjo/cmip5/historical/v20190628'
    ncfile = 'cmip5_obs_historical_obs_mjo_1997-2010_cmmGrid.nc'
    title = 'OBS (GPCP-1-3) \n Pr, NDJFMA, 1997-2010, common grid (2.5x2.5deg)'
    ewr = 2.494024187737836
    pngfilename = 'cmip5_obs_historical_GPCP-1-3_mjo_1997-2010_cmmGrid'

    """
    datadir = '/work/lee1043/imsi/result_test/diagnostic_results/mjo/cmip5/historical/v20190715'
    ncfile = 'cmip5_obs_historical_GPCP-1-2_mjo_1997-2010_cmmGrid.nc'
    title = 'OBS (GPCP-1-2) \n Pr, NDJFMA, 1997-2010, common grid (2.5x2.5deg)'
    ewr = 2.516746230344365
    pngfilename = ncfile.split('.nc')[0]
    """

    imgdir = '.'

    f = cdms2.open(os.path.join(datadir, ncfile))
    d = f('power')
    fout = os.path.join(imgdir, pngfilename)

    plot_power(d, title, fout, ewr=ewr)
