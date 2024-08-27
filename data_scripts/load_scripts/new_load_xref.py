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

        cursor.execute("DELETE FROM biox_xref")
        cursor.execute("ALTER TABLE biox_xref AUTO_INCREMENT = 1")

        genename2featureid = {}
        cursor.execute("SELECT featureId, featureName FROM biox_feature")
        for row in cursor.fetchall():
            feature_id = row[0]
            gene_name = row[1]
            genename2featureid[gene_name] = feature_id

        load_count = 0
        for idx, row in enumerate(dict_reader):
            gene_name = row.get("gene_name")
            xref_db = row.get("xref_db")
            xref_id = row.get("xref_id")

            if not gene_name or gene_name not in genename2featureid:
                utils.graceful_exit(
                    exit_code=1,
                    error_msg=f"Gene name `{gene_name}` on row {idx} not found in biox_feature table or missing.",
                )

            feature_id = genename2featureid[gene_name]

            sql = "INSERT INTO biox_xref (xrefId,xrefSrc,featureId) VALUES "
            cursor.execute(sql, (xref_id, xref_db, feature_id))
            load_count += 1
            LOGGER.debug(f"Row {idx}: Inserted {xref_id}, {xref_db}, {feature_id}")

        cursor.connection.commit()
        LOGGER.info(f"Finished loading {load_count} rows into biox_ref.")

    except Exception as e:
        LOGGER.error(f"An error occurred: {e}")
        LOGGER.error(traceback.format_exc())
        cursor.connection.rollback()

    finally:
        utils.finish(cursor, file_handle)


if __name__ == "__main__":
    main()
