import os
import pkg_resources


def resource_path():
    if "CONDA_PREFIX" in os.environ:
        res_path = os.path.join(os.environ["CONDA_PREFIX"], "share", "pmp")

        # Handle edge case when in conda env but the package is not installed
        # with conda
        if os.path.exists(res_path):
            return res_path

    try:
        res_path = pkg_resources.resource_filename(
            pkg_resources.Requirement.parse("pcmdi_metrics"),
            "share/pmp",
        )
    except Exception:
        res_path = os.path.join(os.getcwd(), "share", "pmp")

    # Should never fail this
    assert os.path.exists(res_path)

    return res_path
