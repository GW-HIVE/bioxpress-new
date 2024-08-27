import traceback
from flask import current_app as app
from sqlalchemy import text
from bioxpress.db import db
import json


def search_cancer(in_json: dict):

    with open("config.json", "r") as config_file:
        config = json.load(config_file)

    try:
        queries = config["queries"]

        # Parse input JSON
        qry_hash = {obj["fieldname"]: obj["fieldvalue"] for obj in in_json["qrylist"]}

        # Determine which query to use
        if qry_hash["dedirection"] != "both":
            sql = queries["query_31"]
        else:
            sql = queries["query_32"]

        # Replace placeholders with actual values
        sql = sql.replace("QVALUE1", qry_hash["cancerid"])
        sql = sql.replace("QVALUE2", qry_hash["featuretype"])
        sql = sql.replace("QVALUE3", qry_hash["dedirection"])
        sql = sql.replace("QVALUE4", qry_hash["cutoff"])

        # If cutoff contains a '|', use another query
        if "|" in qry_hash["cutoff"]:
            sql = queries["query_33"]
            sql = sql.replace("QVALUE1", qry_hash["cancerid"])
            sql = sql.replace("QVALUE2", qry_hash["featuretype"])
            sql = sql.replace("QVALUE3", qry_hash["dedirection"])
            sql = sql.replace("QVALUE4", qry_hash["cutoff"].split("|")[0])
            sql = sql.replace("QVALUE5", qry_hash["cutoff"].split("|")[1])

        # Execute the query
        with db.engine.connect() as conn:
            result = conn.execute(text(sql)).fetchall()

        # Process the result and build the output JSON
        label_list = config["tableheaders"]["cancerview"]["labellist"]
        type_list = config["tableheaders"]["cancerview"]["typelist"]
        obj_list1 = [label_list, type_list]
        obj_list2 = [label_list]

        for row in result:
            obj1 = [""]
            obj2 = [""]
            for j, val in enumerate(row):
                obj1.append(val if type_list[j + 1] == "string" else float(val))
                obj2.append(val)
            obj_list1.append(obj1)
            obj_list2.append(obj2)

        output_json = {
            "taskStatus": 1,
            "inJson": in_json,
            "pageconf": config["pageconf"]["cancerview"],
            "searchresults": obj_list1,
        }

        # Add any additional processing required, such as generating plot data

        return output_json

    except Exception as _:
        log_file = f"/tmp/{config['module'].lower()}-error.log"
        with open(log_file, "w") as fw:
            fw.write(traceback.format_exc())
        return {
            "taskStatus": 0,
            "errorMsg": f"Service error! Please see {log_file} for details.",
        }

def get_cancer_list():

    try:
        # SQL query to get the cancer list
        sql = "SELECT DISTINCT A.id, A.doId, A.doName FROM biox_cancer A, biox_level B WHERE A.id = B.cancerId AND A.id != 1"
        
        # Execute the query
        with db.engine.connect() as conn:
            result = conn.execute(text(sql)).fetchall()

        # Format the result into JSON
        cancer_list = [{"id": row[0], "doid": row[1], "doname": row[2]} for row in result]

        return {"cancerlist": cancer_list, "taskstatus": 1}

    except Exception as e:
        return {"taskstatus": 0, "errormsg": str(e)}
