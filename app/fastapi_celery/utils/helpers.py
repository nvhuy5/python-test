import logging.config

def logging_config(logger: str):
    logging.config.dictConfig({
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '{asctime} {levelname} {message}',
                'style': '{',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'detailed',
            },
        },
        'loggers': {
            f'{logger}': {
                'level': 'DEBUG',
                'handlers': ['console'],
                'propagate': True,
            },
        },
    })
