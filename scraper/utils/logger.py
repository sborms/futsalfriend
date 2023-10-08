import logging
import sys
from logging.handlers import WatchedFileHandler

import structlog


class Logger:
    def __init__(self, log_name, log_file, level) -> None:
        # define basic configuration
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        # define stdout handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.dev.ConsoleRenderer(colors=True)
            )
        )

        # define log file handler
        file_handler = WatchedFileHandler(
            filename=log_file, mode="wt", encoding="utf-8"
        )
        file_handler.setFormatter(
            structlog.stdlib.ProcessorFormatter(
                processor=structlog.processors.JSONRenderer()
            )
        )

        # add handlers to single root logger
        root_logger = structlog.getLogger(log_name)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(file_handler)

        # set logging level
        root_logger.setLevel(level)

        # add logger to class instance
        self.logger = root_logger

    @classmethod
    def get_logger(cls, log_name, log_file, level=logging.INFO):
        return cls(log_name, log_file, level).logger
