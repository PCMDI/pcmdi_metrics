import os
from unittest import mock

from pcmdi_metrics import resources


def test_conda_env(tmpdir):
    conda_prefix = os.path.join(tmpdir, "conda")

    pmp_share_path = os.path.join(conda_prefix, "share", "pmp")

    os.makedirs(pmp_share_path, exist_ok=True)

    with mock.patch.dict(os.environ, {"CONDA_PREFIX": conda_prefix}):
        path = resources.resource_path()

    assert path == os.path.join(tmpdir, "conda", "share", "pmp")


@mock.patch("os.getcwd")
@mock.patch("importlib.metadata.distribution")
def test_conda_env_no_exist(distribution, getcwd, tmpdir):
    # Fix issue when tests are ran against an installed package
    distribution.side_effect = Exception()

    conda_prefix = os.path.join(tmpdir, "conda")

    getcwd_path = os.path.join(tmpdir, "share", "pmp")

    os.makedirs(getcwd_path, exist_ok=True)

    getcwd.return_value = tmpdir

    with mock.patch.dict(os.environ, {"CONDA_PREFIX": conda_prefix}):
        path = resources.resource_path()

    assert path == os.path.join(tmpdir, "share", "pmp")


@mock.patch("importlib.metadata.distribution")
def test_pkg_resources(distribution, tmpdir):
    class DummyDist:
        def locate_file(self, path):
            return str(tmpdir)

    distribution.return_value = DummyDist()

    path = resources.resource_path()

    assert path == str(tmpdir)
