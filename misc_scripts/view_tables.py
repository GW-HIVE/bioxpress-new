from utils import (
    get_db_cursor,
    graceful_exit,
    default_argparse,
    validate_server_arg,
    close_connection,
)


def main():

    parser = default_argparse("view_tables.py")
    options = parser.parse_args()
    if not validate_server_arg(options.server):
        graceful_exit(
            exit_code=1, error_msg=f"Invalid server `{options.server}` provided."
        )

    cursor = get_db_cursor(options.server)

    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()

    if not tables:
        print("No tables found in the database.")
        return

    print("Tables in the database:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        row_count = cursor.fetchone()
        row_count = (
            row_count[0] if row_count is not None else "error grabbing row count"
        )
        print(f"\t- {table[0]}; row count: {row_count}")

    close_connection(cursor)


if __name__ == "__main__":
    main()
