import urllib.request
import requests
import os

import matplotlib.pyplot as plt


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
    if not os.path.isfile("./pmp_logo.png"):
        # setting filename and image URL
        filename = "pmp_logo.png"
        image_url = "https://github.com/PCMDI/pcmdi_metrics/raw/main/share/pcmdi/PMPLogoText_1359x1146px_300dpi.png"

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


def download_archived_results(path, local_dir):
    """ Download file from url to local_dir 
    
    Parameters
    ----------
    path : str 
        Directory path and filename in the PMP results archive in https://github.com/PCMDI/pcmdi_metrics_results_archive
    local_dir : str
        directory path in your local machine to save downloaded file
    """
    os.makedirs(local_dir, exist_ok=True)
    url_head_github_repo = "https://github.com/PCMDI/pcmdi_metrics_results_archive/tree/main/"
    url_head = "https://raw.githubusercontent.com/PCMDI/pcmdi_metrics_results_archive/main/"
    url = url_head + path
    filename = url.split('/')[-1]
    try:
        r = requests.get(url, allow_redirects=True)
        r.raise_for_status()
        local_file = os.path.join(local_dir, filename)
        if os.path.exists(local_file):
            pass
        else:
            with open(local_file, 'wb') as file:
                file.write(r.content)
            print('Download completed:', local_file)
    except:
        print(path, 'not exist in ', url_head_github_repo)
        pass