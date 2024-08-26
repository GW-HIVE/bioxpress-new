from utils import (
    get_db_connection,
    graceful_exit,
    default_argparse,
    validate_server_arg,
    close_connections,
)


def main():

    parser = default_argparse("view_tables.py")
    options = parser.parse_args()
    if not validate_server_arg(options.server):
        graceful_exit(
            exit_code=1, error_msg=f"Invalid server `{options.server}` provided."
        )

    connection = get_db_connection(options.server)
    cursor = connection.cursor()

    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    if not tables:
        print("No tables found in the database.")
        return

    print("Tables in the database:")
    for table in tables:
        print(table[0])

    close_connections(connection, cursor)


if __name__ == "__main__":
    main()
