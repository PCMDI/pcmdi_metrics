import os
from unittest import mock

from pcmdi_metrics.io.base import generateProvenance


def _mock_popen(stdout=b"", stderr=b""):
    proc = mock.MagicMock()
    proc.communicate.return_value = (stdout, stderr)
    return proc


# ---------------------------------------------------------------------------
# Branch selection: conda vs pixi
# ---------------------------------------------------------------------------


@mock.patch("pcmdi_metrics.io.base.Popen")
def test_provenance_conda_branch(mock_popen):
    """Uses conda provenance when PIXI env vars are absent."""
    mock_popen.return_value = _mock_popen()
    env = {"PIXI_ENVIRONMENT_NAME": "", "PIXI_PROJECT_ROOT": ""}
    with mock.patch.dict(os.environ, env):
        prov = generateProvenance(history=False)

    assert "conda" in prov
    assert "pixi" not in prov
    assert "packages" in prov


@mock.patch("pcmdi_metrics.io.base.Popen")
def test_provenance_pixi_branch(mock_popen):
    """Uses pixi provenance when PIXI_ENVIRONMENT_NAME is set."""
    mock_popen.return_value = _mock_popen()
    env = {"PIXI_ENVIRONMENT_NAME": "default", "PIXI_PROJECT_ROOT": "/fake/project"}
    with mock.patch.dict(os.environ, env):
        with mock.patch("pcmdi_metrics.io.base.PIXI", "/fake/pixi"):
            prov = generateProvenance(history=False)

    assert "pixi" in prov
    assert "info" in prov["pixi"]
    assert "list" in prov["pixi"]
    assert "conda" not in prov
    assert "packages" in prov


# ---------------------------------------------------------------------------
# Robustness: no executable available
# ---------------------------------------------------------------------------


@mock.patch("pcmdi_metrics.io.base.Popen", side_effect=FileNotFoundError)
def test_provenance_no_conda_executable(mock_popen):
    """Does not raise when the conda executable is missing."""
    env = {"PIXI_ENVIRONMENT_NAME": "", "PIXI_PROJECT_ROOT": ""}
    with mock.patch.dict(os.environ, env):
        prov = generateProvenance(history=False)

    assert "conda" in prov  # key created even when subprocess fails


@mock.patch("pcmdi_metrics.io.base.Popen", side_effect=FileNotFoundError)
def test_provenance_no_pixi_executable(mock_popen):
    """Does not raise when the pixi executable is missing."""
    env = {"PIXI_ENVIRONMENT_NAME": "default", "PIXI_PROJECT_ROOT": "/fake/project"}
    with mock.patch.dict(os.environ, env):
        with mock.patch("pcmdi_metrics.io.base.PIXI", "/nonexistent/pixi"):
            prov = generateProvenance(history=False)

    assert "pixi" in prov  # key created even when subprocess fails


# ---------------------------------------------------------------------------
# Core provenance keys are always present
# ---------------------------------------------------------------------------


@mock.patch("pcmdi_metrics.io.base.Popen")
def test_provenance_core_keys(mock_popen):
    """Platform, userId, date, and packages keys are always populated."""
    mock_popen.return_value = _mock_popen()
    env = {"PIXI_ENVIRONMENT_NAME": "", "PIXI_PROJECT_ROOT": ""}
    with mock.patch.dict(os.environ, env):
        prov = generateProvenance(history=False)

    for key in ("platform", "userId", "osAccess", "commandLine", "date", "packages"):
        assert key in prov

    assert "OS" in prov["platform"]
    assert "Name" in prov["platform"]
