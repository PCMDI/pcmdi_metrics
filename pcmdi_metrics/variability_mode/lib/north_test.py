import os

import matplotlib.pyplot as plt
import numpy as np


def north_test(
    solver,
    outdir: str = ".",
    output_filename: str = "north_test",
    plot_title: str = None,
    neigs: int = 10,
    vfscaled: bool = True,
) -> None:
    """Typical errors for eigenvalues.
    The method of North et al. (1982) is used to compute the typical error for each eigenvalue. It is assumed that the number of times in the input data set is the same as the number of independent realizations. If this assumption is not valid then the result may be inappropriate.
    Detailed description can be found here:
    https://ajdawson.github.io/eofs/latest/api/eofs.xarray.html?highlight=north#eofs.xarray.Eof.northTest

    Parameters
    ----------
    solver : An Eof instance.
        Detailed description for Eof instance:
        https://ajdawson.github.io/eofs/latest/api/eofs.xarray.html?highlight=north#eofs.xarray.Eof
    outdir : str
        output directory path, by default current directory
    output_filename : str
        output file name, by default "north_test"
    plot_title : str, optional
        _description_, by default None
    neigs : int, optional
        _description_, by default 10
    vfscaled : bool, optional
        _description_, by default True
    """

    errors = solver.northTest(neigs=neigs, vfscaled=vfscaled)
    fracs = solver.varianceFraction()

    fig = plt.figure()
    ax = fig.add_subplot(111)

    if plot_title is not None:
        fig.suptitle(plot_title, fontsize=14, fontweight="bold")

    datalen = len(errors)

    if datalen > 20:
        datalen = 20

    x = range(1, datalen + 1)
    y = np.array(fracs[0:datalen] * 100)
    ye = np.array(errors[0:datalen] * 100)

    ax.set_title("Eigenvalue Spectrum with North test")

    plt.xlabel("EOF mode #", fontsize=14)
    plt.ylabel("% of variance", fontsize=14)

    plt.plot(x, y)
    plt.errorbar(x, y, yerr=ye)

    plt.savefig(os.path.join(outdir, output_filename + ".png"))

    ofile = open(os.path.join(outdir, output_filename + ".txt"), "w", encoding="utf-8")
    for i in range(0, datalen):
        ofile.write(
            f"EOF{i + 1}: frac (%), error (%): {fracs[i] * 100.0}, {errors[i] * 100.0}\n"
        )
