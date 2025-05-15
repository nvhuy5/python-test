import logging.config
import colorlog
from pathlib import Path
import tempfile


def logging_config(logger: str):
    log = logging.getLogger(logger)

    # Clear old handlers
    if log.hasHandlers():
        log.handlers.clear()

    # Create a celery_logs directory in temporary directory
    log_dir = Path(tempfile.gettempdir()) / "celery_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "celery_worker.log"

    log_format = (
        "\n%(log_color)s=== %(asctime)s - [%(processName)s - %(levelname)s] ===\n"
        "%(message)s\n"
        "%(log_color)s==========================================\n"
    )

    logging.config.dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "colorful": {
                "()": "colorlog.ColoredFormatter",
                "format": log_format,
                "log_colors": {
                    "DEBUG": "cyan",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "red",
                    "CRITICAL": "bold_red",
                },
                "style": "%",
            },
            "beautiful": {
                "format": "\n=== %(asctime)s - [%(processName)s] %(levelname)s ===\n%(message)s\n==========================================\n",
                "style": "%",
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "colorful",
            },
            "file": {
                "level": "INFO",
                "class": "logging.FileHandler",
                "filename": str(log_file),
                "formatter": "beautiful",
            },
        },
        "loggers": {
            f"{logger}": {
                "level": "DEBUG",
                "handlers": ["console", "file"],
                "propagate": False,
            },
        },
    })
