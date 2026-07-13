from __future__ import annotations

import os
import runpy
from pathlib import Path

from setuptools import build_meta as _orig
from setuptools.build_meta import *  # noqa: F401,F403 - re-export PEP 517 hooks

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_GENERATOR = _PROJECT_ROOT / "share" / "setup_default_args.py"


def _run_prebuild_generator() -> None:
    """Run the script that (re)generates share/DefArgsCIA.json if present.

    Mirrors the behavior previously invoked in setup.py before packaging.
    The script writes DefArgsCIA.json into the share directory.
    """
    if _GENERATOR.is_file():
        # Execute in-place with cwd=share to preserve original behavior
        share_dir = _GENERATOR.parent
        cwd = os.getcwd()
        try:
            os.chdir(share_dir)
            # runpy.run_path executes the script as __main__ without spawning a new process
            runpy.run_path(str(_GENERATOR), run_name="__main__")
        finally:
            os.chdir(cwd)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):  # type: ignore[override]
    _run_prebuild_generator()
    return _orig.build_wheel(wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory, config_settings=None):  # type: ignore[override]
    _run_prebuild_generator()
    return _orig.build_sdist(sdist_directory, config_settings)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):  # type: ignore[override]
    # PEP 660 editable install hook (pip -e). Ensure the file exists here too.
    _run_prebuild_generator()
    return _orig.build_editable(wheel_directory, config_settings, metadata_directory)


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):  # type: ignore[override]
    _run_prebuild_generator()
    return _orig.prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):  # type: ignore[override]
    _run_prebuild_generator()
    return _orig.prepare_metadata_for_build_editable(
        metadata_directory, config_settings
    )
