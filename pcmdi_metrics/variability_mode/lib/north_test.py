import os

import matplotlib.pyplot as plt
import numpy as np


def north_test(solver, mode, season, obs_name, osyear, oeyear, outdir):
    errors = solver.northTest(vfscaled=True)
    fracs = solver.varianceFraction()

    title_string = f"{mode}, {season}, {obs_name} {osyear}-{oeyear}"

    fig = plt.figure()
    fig.suptitle(title_string, fontsize=14, fontweight="bold")
    ax = fig.add_subplot(111)

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

    plt.savefig(
        os.path.join(
            outdir,
            f"EG_Spec_North_test_{mode}_{season}_{obs_name}_{osyear}-{oeyear}.png",
        )
    )

    ofile = open(
        os.path.join(
            f"EG_Spec_North_test_{mode}_{season}_{obs_name}_{osyear}-{oeyear}.txt", "w"
        )
    )
    for i in range(0, datalen):
        ofile.write(
            "EOF"
            + str(i + 1)
            + ": frac (%), error (%): "
            + str(fracs[i] * 100.0)
            + ", "
            + str(errors[i] * 100.0)
            + "\n"
        )
