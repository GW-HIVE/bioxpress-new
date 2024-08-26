import pymysql
from pymysql.connections import Connection
from pymysql.cursors import Cursor
from typing import Literal, Optional, NoReturn
import json
import sys
import argparse
from argparse import ArgumentParser


def get_config_json() -> dict:

    with open("../api/config.json", "r") as config:
        return_data = json.load(config)

    if not isinstance(return_data, dict):
        graceful_exit(
            exit_code=1,
            error_msg=f"Expected config to be type `dict`, got `{type(return_data)}`.",
        )

    return return_data


def get_db_connection(server: Literal["tst", "prd"]) -> Connection[Cursor]:

    config_json = get_config_json()
    host = "127.0.0.1"
    db_name = config_json["dbinfo"]["dbname"]
    port = config_json["dbinfo"]["port"][server]
    username = config_json["dbinfo"][db_name]["user"]
    password = config_json["dbinfo"][db_name]["password"]

    try:
        connection = pymysql.connect(
            host=host, port=port, user=username, password=password, database=db_name
        )
    except Exception as e:
        graceful_exit(exit_code=1, error_msg=str(e))

    return connection


def close_connections(connection: Connection, cursor: Cursor) -> None:
    connection.close()
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
