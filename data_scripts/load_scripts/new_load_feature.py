from data_scripts import utils
import traceback
from pathlib import Path

IN_FILE = "../../data/bioxpress-final.xref.csv"
LOGGER = utils.setup_logger(Path(__file__).stem, "load_scripts")


def main() -> None:

    parser = utils.default_argparse("new_load_feature.py")
    options = parser.parse_args()

    if not utils.validate_server_arg(options.server):
        utils.graceful_exit(
            exit_code=1,
            error_msg=f"Invalid server `{options.server}` provided.",
            logger=LOGGER,
        )

    cursor = utils.get_db_cursor(options.server)
    dict_reader, file_handle = utils.get_csv_reader(IN_FILE)

    try:
        # Clear the table and reset auto-increment
        cursor.execute("DELETE FROM biox_feature")
        cursor.execute("ALTER TABLE biox_feature AUTO_INCREMENT = 1")

        seen = set()
        load_count = 0
        for idx, row in enumerate(dict_reader):
            gene_name = row.get("gene_name")

            # TODO : retaining original logic, even though these are not used
            xref_db = row.get("xref_db")
            xref_id = row.get("xref_id")

            if not gene_name:
                utils.graceful_exit(
                    exit_code=1,
                    error_msg=f"Missing gene_name on row `{idx}`.",
                    logger=LOGGER,
                )

            if gene_name not in seen:
                sql = "INSERT INTO biox_feature (featureName, featureType) VALUES "
                sql += "('%s','%s')" % (gene_name, "mrna")
                cursor.execute(sql)
                load_count += 1
                LOGGER.info(f"{load_count}, {sql}")
                seen.add(gene_name)

        cursor.connection.commit()
        LOGGER.info(f"Finished loading {load_count} rows.")

    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")
        LOGGER.error(traceback.format_exc())
        cursor.connection.rollback()

    finally:
        utils.finish(cursor, file_handle)


if __name__ == "__main__":
    main()
