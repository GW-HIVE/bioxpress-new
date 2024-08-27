import json
from flask import current_app as app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from bioxpress.db import db
from typing import Any


def get_stats() -> dict:

    outJson: dict[Any, Any] = {"titles": {}, "taskstatus": 1}

    try:
        # Query to fetch titles from biox_stat
        query = text("SELECT id, title FROM biox_stat")
        result = db.session.execute(query)

        if result:
            # theres only one row but iterating for completeness
            for row in result:
                outJson["titles"][row.id] = row.title

                obj = json.loads(row.jsonstring)
                outJson["dataframe"] = [obj["fieldnames"], obj["fieldtypes"]] + obj[
                    "dataframe"
                ]

        else:
            outJson["taskstatus"] = 0
            outJson["errormsg"] = "No statistics found."

    except ValueError as e:
        app.logger.error(f"ValueError: {e}")
        outJson["taskstatus"] = 0
        outJson["errormsg"] = str(e)

    except SQLAlchemyError as e:
        app.logger.error(f"Database error: {str(e)}", exc_info=True)
        outJson["taskstatus"] = 0
        outJson["errormsg"] = f"Database error: {str(e)}"

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        outJson["taskstatus"] = 0
        outJson["errormsg"] = f"Unexpected error: {str(e)}"

    return outJson
