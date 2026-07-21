"""Helpers for running `process_qbo_mjo_metrics` under multiprocessing."""

import logging
import sys
import time

from .compute_qbo_mjo_metrics import process_qbo_mjo_metrics


def configure_logger(filename):
    """Create a logger that writes INFO-level messages to a file.

    Parameters
    ----------
    filename : str
        Path to the log file.

    Returns
    -------
    logging.Logger
        Root logger configured with a `logging.FileHandler` at ``filename``.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(filename)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


class LoggerWriter:
    """File-like adapter that redirects writes (e.g. `sys.stdout`) to a `logging.Logger`.

    Parameters
    ----------
    logger : logging.Logger
        Logger to forward writes to.
    level : int, optional
        Logging level to log each write at. Default is ``logging.INFO``.
    """

    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level

    def write(self, message):
        """Log `message` if it is non-blank.

        Parameters
        ----------
        message : str
            Text to log.
        """
        if message.strip() != "":
            self.logger.log(self.level, message.strip())

    def flush(self):
        """No-op, present for file-like interface compatibility."""
        pass


def process(params):
    """Run `process_qbo_mjo_metrics` for one model/member with logging redirected to a file.

    Intended as the per-task target for `multiprocessing.Pool.starmap` in
    `qbo_mjo_driver.py`'s parallel mode. Redirects `sys.stdout` to
    ``params["log_file"]`` for the duration of the call.

    Parameters
    ----------
    params : dict
        Parameters dictionary passed through to `process_qbo_mjo_metrics`.
        Must additionally contain ``"log_file"``, the path to write log
        output to.
    """
    exp = params["exp"]
    model = params["model"]
    member = params["member"]
    log_file = params["log_file"]

    logger = configure_logger(log_file)
    logger.info(
        f'Starting process for {exp}, {model}, {member} at {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())}'
    )

    # Redirect stdout to logger
    sys.stdout = LoggerWriter(logger, logging.INFO)

    start_time = time.time()

    # Call detection function
    process_qbo_mjo_metrics(params)

    end_time = time.time()

    print(
        f'Process finished at {time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(end_time))}. Elapsed time: {end_time - start_time} seconds.'
    )
    logger.info("Done")
