import logging
from logging.handlers import RotatingFileHandler


class VLCync_Logger:
    @staticmethod
    def get_logger(type: str) ->logging.Logger:
        logger = logging.getLogger('VLCync')
        logger.propagate=False
        logger.setLevel(logging.DEBUG)
        form = logging.Formatter('%(name)s-%(type)s| %(asctime)s | %(levelname)-5s: %(message)s')
        if not logger.hasHandlers():
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(form)
            logger.addHandler(console_handler)

            file_handler = RotatingFileHandler(f"VLCync_{type}.log", backupCount=3)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(form)
            logger.addHandler(file_handler)

        return logging.LoggerAdapter(logger, extra={"type": type})