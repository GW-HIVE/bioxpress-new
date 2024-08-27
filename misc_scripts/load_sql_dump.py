from pathlib import Path
from typing import Literal
from utils import (
    get_config_json,
    graceful_exit,
    default_argparse,
    validate_server_arg,
    setup_logger,
)
import traceback
from pymysql.cursors import Cursor
import subprocess

# Path to the SQL dump file to be loaded into the MySQL database
IN_FILE = "../sql_dump/bioxpress_prd.dump.sql"
# Logger instance to track script execution
LOGGER = setup_logger(Path(__file__).stem)


def load_sql_dump(
    config_json: dict, server: Literal["tst", "prd"], dump_file: str
) -> None:
    """Loads an SQL dump file into the connected MySQL database.

    This function uses a subprocess to execute the MySQL command that imports
    the SQL dump file into the database. It logs the process and any errors
    encountered during execution.
    """
    LOGGER.info(f"Loading SQL dump from file: {dump_file}.")

    host = "127.0.0.1"
    db_name = config_json["dbinfo"]["dbname"]
    port = int(config_json["dbinfo"]["port"][server])
    username = config_json["dbinfo"][db_name]["user"]
    password = config_json["dbinfo"][db_name]["password"]

    command = (
        f"mysql -u {username} "
        f"-p{password} "
        f"-h {host} "
        f"-P {port} "
        f"{db_name} < {dump_file}"
    )
    LOGGER.debug(f"command: {command}")

    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            stderr=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        if result.returncode == 0:
            LOGGER.info("SQL dump loaded successfully.")
        else:
            LOGGER.error(f"Error loading SQL dump: {result.stderr.decode('utf-8')}")

    except subprocess.CalledProcessError as e:
        LOGGER.error(f"Subprocess error: {e}")
        LOGGER.error(traceback.format_exc())

    except Exception as e:
        LOGGER.error(f"Subprocess error: {e}")
        LOGGER.error(traceback.format_exc())


def main() -> None:

    parser = default_argparse("view_tables.py")
    options = parser.parse_args()
    if not validate_server_arg(options.server):
        graceful_exit(
            exit_code=1, error_msg=f"Invalid server `{options.server}` provided."
        )

    config_json = get_config_json()

    load_sql_dump(config_json, options.server, IN_FILE)


if __name__ == "__main__":
    main()
