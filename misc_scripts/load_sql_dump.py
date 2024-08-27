from pathlib import Path
from utils import (
    get_db_cursor,
    graceful_exit,
    default_argparse,
    validate_server_arg,
    close_connection,
    setup_logger,
)
import traceback
from pymysql.cursors import Cursor
import subprocess

# Path to the SQL dump file to be loaded into the MySQL database
IN_FILE = "../sql_dump/bioxpress_prd.dump.sql"
# Logger instance to track script execution
LOGGER = setup_logger(Path(__file__).stem)


def load_sql_dump(cursor: Cursor, dump_file: str) -> None:
    """Loads an SQL dump file into the connected MySQL database.

    This function uses a subprocess to execute the MySQL command that imports
    the SQL dump file into the database. It logs the process and any errors
    encountered during execution.

    Parameters
    ----------
    cursor : pymysql.cursors.Cursor
        A cursor connected to the target MySQL database.
    dump_file : str
        The path to the SQL dump file to be loaded.
    """
    LOGGER.info(f"Loading SQL dump from file: {dump_file}.")
    command = f"mysql -u {cursor.connection.user} -p {cursor.connection.password} -h {cursor.connection.host} -P {cursor.connection.port} {cursor.connection.db} < {dump_file}"

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
        cursor.connection.rollback()

    except Exception as e:
        LOGGER.error(f"Subprocess error: {e}")
        LOGGER.error(traceback.format_exc())
        cursor.connection.rollback()


def main() -> None:

    parser = default_argparse("view_tables.py")
    options = parser.parse_args()
    if not validate_server_arg(options.server):
        graceful_exit(
            exit_code=1, error_msg=f"Invalid server `{options.server}` provided."
        )

    cursor = get_db_cursor(options.server)

    try:
        load_sql_dump(cursor, IN_FILE)

    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")
        LOGGER.error(traceback.format_exc())
        cursor.connection.rollback()

    finally:
        close_connection(cursor)


if __name__ == "__main__":
    main()
