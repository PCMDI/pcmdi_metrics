#  put here the impor calls to expose whatever we want to the user
import logging
LOG_LEVEL = logging.INFO
logging.getLogger("pcmdi_metrics").setLevel(logging.WARNING)
import io  # noqa
import pcmdi  # noqa
from version import __version__, __git_sha1__, __git_tag_describe__  # noqa
