import pymysql
from pymysql.cursors import Cursor
from typing import Literal, Optional, NoReturn
import json
import sys
import argparse
from argparse import ArgumentParser
import traceback
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


def close_connection(cursor: Cursor) -> None:
    cursor.close()


def graceful_exit(exit_code: int = 0, error_msg: Optional[str] = None) -> NoReturn:
    """Gracefully exits the program with an exit code.

    Parameters
    ----------
    exit_code : int, optional
        The exit code.
    error_msg : str | None, optional
        The error message to print before exiting.
    """
    if exit_code != 0:
        if error_msg is not None:
            print(f"{error_msg}")
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


def setup_logger(script: str) -> Logger:
    """Sets up a logger for a specific script.

    Parameters
    ----------
    script : str
        The name of the script using the logger, used to generate the log file name.

    Returns
    -------
    Logger
        Configured logger instance.
    """
    logger = logging.getLogger(script)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    file_handler = logging.FileHandler(
        os.path.join(CURRENT_DIR, "logging", f"{script}.log")
    )

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger
