from os import path
import matplotlib.pyplot as plt
import urllib.request


def add_logo(fig, ax, rect=None):
    """
    Parameters
    ----------
    - `fig`: `matplotlib.figure` instance to which the portrait plot is plotted.
             If not provided, use current axes or create a new one.  Optional.
    - `rect`: sequence of float. The dimensions [left, bottom, width, height] of the logo.
              All quantities are in fractions of figure width and height.

    Return
    ------
    - `fig`: matplotlib component for figure
    """
    if rect is None:
        rect = [0.75, 0.75, 0.2, 0.2]

    # Download image if not exist -- later, change to use egg_path!
    if not path.isfile("./pmp_logo.png"):
        # setting filename and image URL
        filename = "pmp_logo.png"
        image_url = "https://github.com/PCMDI/pcmdi_metrics/raw/master/share/pcmdi/PMPLogoText_1359x1146px_300dpi.png"

        # calling urlretrieve function to get resource
        urllib.request.urlretrieve(image_url, filename)

    im = plt.imread("./pmp_logo.png")

    # Place the image in the upper-right corner of the figure
    # --------------------------------------------------------
    # We're specifying the position and size in _figure_ coordinates, so the image
    # will shrink/grow as the figure is resized. Remove "zorder=-1" to place the
    # image in front of the axes.
    # rect in add_axes: [left, bottom, width, height], fractions of figure width and height
    newax = fig.add_axes(rect, anchor="NE")

    newax.imshow(im)
    newax.axis("off")

    return fig, ax
