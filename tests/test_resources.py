import os
from unittest import mock

from pcmdi_metrics import resources


def test_conda_env(tmpdir):
    conda_prefix = os.path.join(tmpdir, "conda")

    pmp_share_path = os.path.join(conda_prefix, "share", "pmp")

    os.makedirs(pmp_share_path)

    with mock.patch.dict(os.environ, {"CONDA_PREFIX": conda_prefix}):
        path = resources.resource_path()

    assert path == os.path.join(tmpdir, "conda", "share", "pmp")


@mock.patch("os.getcwd")
@mock.patch("pkg_resources.resource_filename")
def test_conda_env_no_exist(resource_filename, getcwd, tmpdir):
    # Fix issue when tests are ran against an installed package
    resource_filename.side_effect = Exception()

    conda_prefix = os.path.join(tmpdir, "conda")

    getcwd_path = os.path.join(tmpdir, "share", "pmp")

    os.makedirs(getcwd_path)

    getcwd.return_value = tmpdir

    with mock.patch.dict(os.environ, {"CONDA_PREFIX": conda_prefix}):
        path = resources.resource_path()

    assert path == os.path.join(tmpdir, "share", "pmp")


@mock.patch("pkg_resources.Requirement.parse")
@mock.patch("pkg_resources.resource_filename")
def test_pkg_resources(resource_filename, parse, tmpdir):
    resource_filename.return_value = str(tmpdir)

    path = resources.resource_path()

    assert path == str(tmpdir)
