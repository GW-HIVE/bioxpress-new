from io import TextIOWrapper
import pymysql
from pymysql.cursors import Cursor
from typing import Literal, Optional, NoReturn
import json
import sys
import argparse
from argparse import ArgumentParser
import traceback
from csv import DictReader
from typing import Tuple
from logging import Logger
import logging
import os

CURRENT_DIR = os.path.dirname(__file__)


def get_config_json() -> dict:

    with open("../api/config.json", "r") as config:
        return_data = json.load(config)

    if not isinstance(return_data, dict):
        graceful_exit(
            exit_code=1,
            error_msg=f"Expected config to be type `dict`, got `{type(return_data)}`.",
        )

    return return_data


def get_db_cursor(server: Literal["tst", "prd"]) -> Cursor:

    config_json = get_config_json()
    host = "127.0.0.1"
    db_name = config_json["dbinfo"]["dbname"]
    port = int(config_json["dbinfo"]["port"][server])
    username = config_json["dbinfo"][db_name]["user"]
    password = config_json["dbinfo"][db_name]["password"]

    try:
        connection = pymysql.connect(
            host=host, port=port, user=username, password=password, database=db_name
        )
    except Exception as e:
        graceful_exit(exit_code=1, error_msg=f"{traceback.format_exc()}\n{e}")

    return connection.cursor()


def get_csv_reader(path: str) -> Tuple[DictReader, TextIOWrapper]:
    f = open(path, "r")
    return DictReader(f), f


def finish(cursor: Cursor, file: TextIOWrapper) -> None:
    cursor.close()
    file.close()


def graceful_exit(
    exit_code: int = 0, error_msg: Optional[str] = None, logger: Optional[Logger] = None
) -> NoReturn:
    if exit_code != 0:
        if error_msg is not None:
            if logger:
                logger.info(error_msg)
            else:
                print(error_msg)
        if logger:
            logger.info(f"exit code: {exit_code}")
        else:
            print(f"exit code: {exit_code}")
    print("Exiting...")
    sys.exit(exit_code)


def default_argparse(prog: str) -> ArgumentParser:
    parser = argparse.ArgumentParser(prog=prog)
    parser.add_argument("server", help="tst/prd")
    return parser


def validate_server_arg(server: str) -> bool:
    if server in {"tst", "prd"}:
        return True
    return False


def setup_logger(script: str, category: Literal["load_scripts"]) -> Logger:
    """Sets up a logger for a specific script.

    Parameters
    ----------
    script : str
        The name of the script using the logger, used to generate the log file name.
    category : Literal["load_scripts"]
        The category of calling script. Used to construct log file path.

    Returns
    -------
    Logger
        Configured logger instance.
    """
    logger = logging.getLogger(script)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(
        os.path.join(CURRENT_DIR, "logging", category, f"{script}.log")
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
