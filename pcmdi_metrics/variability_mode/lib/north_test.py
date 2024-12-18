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
    """
    Compute typical errors for eigenvalues using the method of North et al. (1982).

    This function calculates the typical error for each eigenvalue based on the
    assumption that the number of time steps in the input dataset is equal to the
    number of independent realizations. If this assumption is not valid, the results
    may be inappropriate. For detailed information, refer to the documentation:
    https://ajdawson.github.io/eofs/latest/api/eofs.xarray.html?highlight=north#eofs.xarray.Eof.northTest

    Parameters
    ----------
    solver : Eof
        An instance of the Eof class used for the computation.
        For more details, see:
        https://ajdawson.github.io/eofs/latest/api/eofs.xarray.html?highlight=north#eofs.xarray.Eof
    outdir : str, optional
        The output directory path. Default is the current directory (".").
    output_filename : str, optional
        The name of the output file. Default is "north_test".
    plot_title : str, optional
        The title for the plot. Default is None.
    neigs : int, optional
        The number of eigenvalues to consider. Default is 10.
    vfscaled : bool, optional
        A flag indicating whether the eigenvalues should be scaled. Default is True.

    Returns
    -------
    None
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
