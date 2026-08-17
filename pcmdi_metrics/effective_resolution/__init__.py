"""Effective resolution metric computation.

This module estimates the *effective* (dynamical) resolution of an
atmospheric model -- the smallest spatial scale it plausibly represents --
from the kinetic energy spectra of the rotational and divergent parts of the
horizontal wind, following Klaver et al. (2020).

Unlike the *nominal* resolution, which is just the mesh size, the effective
resolution reflects how far down the spectrum the model's dynamics remain
credible.  Scales below it are affected by parameterisation, numerical
diffusion, interpolation and anti-aliasing filters, and should be disregarded
in interpretational climate studies.

References
----------
Klaver, R., Haarsma, R., Vidale, P. L., & Hazeleger, W. (2020). Effective
    resolution in high resolution global atmospheric models for climate
    studies. *Atmospheric Science Letters*, 21, e952.
    https://doi.org/10.1002/asl.952
"""

from .lib import (  # noqa
    compute_effective_resolution,
    process_effective_resolution,
)

__all__ = ["compute_effective_resolution", "process_effective_resolution"]
