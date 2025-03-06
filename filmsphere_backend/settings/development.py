import os
from .base import *
from pathlib import Path

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# CORS
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = ["http://localhost:5173"]
CSRF_TRUSTED_ORIGINS = ['http://localhost:5173']


# Define the base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ensure logs directory exists
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Logging settings for production
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} [{name}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        # Logging for core (auth app)
        "core_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "core.log",
            "formatter": "verbose",
        },
        # Logging for movie app
        "movie_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "movie.log",
            "formatter": "verbose",
        },
        # Logging for booking app
        "booking_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": LOG_DIR / "booking.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "core": {
            "handlers": ["core_file"],
            "level": "INFO",
            "propagate": False,
        },
        "movie": {
            "handlers": ["movie_file"],
            "level": "INFO",
            "propagate": False,
        },
        "booking": {
            "handlers": ["booking_file"],
            "level": "INFO",
            "propagate": False,
        },
    },
}