import json
from flask import current_app as app
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text
from bioxpress import db
from typing import Any


def get_stats(in_json: dict) -> dict:

    outJson: dict[Any, Any] = {"titles": {}, "taskstatus": 1}

    try:
        # Query to fetch titles from biox_stat
        titles_query = text("SELECT id, title FROM biox_stat")
        titles_result = db.session.execute(titles_query)

        for row in titles_result:
            outJson["titles"][row.id] = row.title

        # Query to fetch the specific stat data
        stat_id = in_json.get("statid")
        if not stat_id:
            outJson["taskstatus"] = 0
            outJson["errormsg"] = "Missing 'statid' in input JSON"

        stat_query = text("SELECT jsonstring FROM biox_stat WHERE id = :stat_id")
        stat_result = db.session.execute(stat_query, {"stat_id": stat_id}).fetchone()

        if stat_result:
            obj = json.loads(stat_result.jsonstring)
            outJson["dataframe"] = [obj["fieldnames"], obj["fieldtypes"]] + obj[
                "dataframe"
            ]
        else:
            outJson["taskstatus"] = 0
            outJson["errormsg"] = f"No stats found for id {stat_id}"

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
