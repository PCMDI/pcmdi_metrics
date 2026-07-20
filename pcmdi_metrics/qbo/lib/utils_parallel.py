import logging
import sys
import time

from compute_qbo_mjo_metrics import process_qbo_mjo_metrics


# Configure the logger
def configure_logger(filename):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(filename)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger


# Redirect stdout to logger
class LoggerWriter:
    def __init__(self, logger, level=logging.INFO):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.strip() != "":
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass


def process(params):
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
