import glob
import os

import xarray as xr
from lib_mjo import calculate_ewr
from plot_wavenumber_frequency_power import plot_power


def main():
    # mip = 'cmip5'
    mip = "cmip6"
    exp = "historical"
    version = "v20190710"
    period = "1985-2004"
    datadir = (
        "/p/user_pub/pmp/pmp_results/pmp_v1.1.2/diagnostic_results/mjo/"
        + mip
        + "/historical/"
        + version
    )
    imgdir = "/work/lee1043/imsi/result_test/mjo_metrics/plot_test"
    # imgdir = '/p/user_pub/pmp/pmp_results/pmp_v1.1.2/graphics/mjo/'+mip+'/historical/'+version

    os.makedirs(imgdir, exist_ok=True)

    ncfile_list = glob.glob(os.path.join(datadir, "*.nc"))

    # get list of models
    models_list = sorted(
        [r.split("/")[-1].split(".")[0].split("_")[1] for r in ncfile_list]
    )
    # remove repeat
    models_list = list(dict.fromkeys(models_list))
    # remove obs
    models_list.remove("obs")

    print(models_list)

    for model in models_list:
        ncfile_list_model = glob.glob(os.path.join(datadir, "*" + model + "*.nc"))
        runs_list = sorted(
            [r.split("/")[-1].split(".")[0].split("_")[3] for r in ncfile_list_model]
        )
        print(model, runs_list)
        d_runs = []
        for run in runs_list:
            try:
                ncfile = (
                    "_".join([mip, model, exp, run, "mjo", period, "cmmGrid"]) + ".nc"
                )
                ds = xr.open_dataset(os.path.join(datadir, ncfile))
                d = ds["power"]
                d_runs.append(d)
                title = (
                    mip.upper()
                    + ": "
                    + model
                    + " ("
                    + run
                    + ") \n Pr, NDJFMA, "
                    + period
                    + ", common grid (2.5x2.5deg)"
                )
                # E/W ratio
                ewr, eastPower, westPower = calculate_ewr(d)
                # plot prepare
                pngfilename = ncfile.split(".nc")[0]
                fout = os.path.join(imgdir, pngfilename)
                # plot
                plot_power(d, title, fout, ewr)
                ds.close()
            except Exception:
                print(model, run, "cannnot load")
                pass


if __name__ == "__main__":
    main()
