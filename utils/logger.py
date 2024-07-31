import re
import sys

from loguru import logger


def formatter(record, format_string):
    end = record["extra"].get("end", "\n")
    return format_string + end + "{exception}"


def logging_setup():
    format_info = "<green>{time:HH:mm:ss.SS}</green> <blue>{level}</blue> <level>{message}</level>"
    logger.add(sys.stdout, colorize=True, format=lambda record: formatter(record, format_info), level="INFO")


def clean_brackets(raw_str):
    clean_text = re.sub(brackets_regex, '', raw_str)
    return clean_text


brackets_regex = re.compile(r'<.*?>')

logging_setup()
