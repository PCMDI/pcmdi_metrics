#  put here the import calls to expose whatever we want to the user
import logging

LOG_LEVEL = logging.DEBUG
plog = logging.getLogger("pcmdi_metrics")
# create console handler
ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)
# create formatter and add it to the handlers
formatter = logging.Formatter(
    "%(levelname)s::%(asctime)s::%(name)s:: %(message)s", datefmt="%Y-%m-%d %H:%M"
)
ch.setFormatter(formatter)
# add the handler to the logger
plog.addHandler(ch)
plog.setLevel(LOG_LEVEL)
from . import io  # noqa

# from . import pcmdi  # noqa
# from . import mean_climate  # noqa
from .version import __git_sha1__, __git_tag_describe__, __version__  # noqa
