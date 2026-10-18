import sys
import logging
from logging.config import dictConfig
import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
LOG_DIR = os.path.join(BASE_DIR, "log")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_CONFIG = {
    "version": 1,  # 固定值，日志配置规范版本号，只能写1
    "disable_existing_loggers": False,  # 保留第三方库自带logger(如requests)，False是项目常用

    "formatters": {
        # 控制台用格式：简短，只显示文件名，终端看着清爽
        "console_fmt": {
            "format": "%(asctime)s %(name)s %(funcName)s [%(filename)s:%(lineno)d] %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        },
        # 文件日志格式：完整，带文件全路径，排查bug时定位代码
        "file_fmt": {
            "format": "%(asctime)s %(name)s %(funcName)s [%(pathname)s line:%(lineno)d] %(levelname)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S"
        }
    },

    "handlers": {
        # 处理器1：输出到终端
        "console_handler": {
            "class": "logging.StreamHandler",
            "formatter": "console_fmt",
            "level": "INFO",
            "stream": "ext://sys.stdout"
        },
        # 处理器2：输出到文件，按大小滚动切割日志，防止单文件无限变大
        "file_handler": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "file_fmt",
            "level": "INFO",
            "filename":os.path.join(BASE_DIR, "log", "app.log"),
            "maxBytes": 5 * 1024 * 1024,  # 单个日志最大5MB
            "backupCount": 5,             # 最多保留5份旧日志，超出自动删除最早
            "encoding": "utf-8"
        }
    },

    "loggers": {
        # Logger1：仅输出终端，不写入文件
        "logger_console": {
            "handlers": ["console_handler"],
            "level": "INFO",
            "propagate": False  # False：日志不再向上传递给root，避免重复打印
        },
        # Logger2：仅写入日志文件，不在终端打印
        "logger_file": {
            "handlers": ["file_handler"],
            "level": "INFO",
            "propagate": False
        },
        # Logger3：终端 + 文件同时输出
        "logger_both": {
            "handlers": ["console_handler", "file_handler"],
            "level": "INFO",
            "propagate": False
        }
    },

    # root根日志器兜底，这里不挂载handler，防止意外重复输出
    "root": {
        "handlers": [],
        "level": "WARNING"
    }
}
