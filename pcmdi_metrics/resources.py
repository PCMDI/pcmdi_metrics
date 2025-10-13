import os
from importlib import metadata


def resource_path():
    if "CONDA_PREFIX" in os.environ:
        res_path = os.path.join(os.environ["CONDA_PREFIX"], "share", "pmp")

        # Handle edge case when in conda env but the package is not installed
        # with conda
        if os.path.exists(res_path):
            return res_path

    try:
        dist = metadata.distribution("pcmdi_metrics")
        # Use importlib.metadata to locate data-files installed with the
        # distribution
        res_path = str(dist.locate_file("share/pmp"))
    except Exception:
        res_path = os.path.join(os.getcwd(), "share", "pmp")

    # Should never fail this
    assert os.path.exists(res_path)

    return res_path
