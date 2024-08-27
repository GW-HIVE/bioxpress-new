import os
import json
import datetime
import time
from flask import current_app as app
from sqlalchemy import text
from bioxpress.db import db
import traceback


def dump_csv_file(data_frame, server_json, file_prefix):
    time_stamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
    output_file = os.path.join(server_json["pathinfo"]["tmppath"], f"{file_prefix}{time_stamp}.csv")

    with open(output_file, "w") as fw:
        for row in data_frame:
            fw.write(",".join(map(str, row)) + "\n")

    os.chmod(output_file, 0o777)

    return f"{file_prefix}{time_stamp}.csv"


def get_data_set_table(config_json, field_value, dataset_id, exclude_field_list):
    cur = db.session.execute(
        text(config_json["queries"]["query_4"].replace("QVALUE", str(dataset_id)))
    )
    field_info = {"name": {}, "type": {}}
    field_type = {"string": {}, "numeric": {}}

    for row in cur.fetchall():
        field_info["name"][row[0]] = row[1]
        field_info["type"][row[0]] = row[2]

    sql = config_json["queries"]["query_41"].replace("QVALUE1", str(dataset_id)).replace("QVALUE2", field_value)
    records = {}
    cur = db.session.execute(text(sql))

    for row in cur.fetchall():
        if row[0] not in records:
            records[row[0]] = {}
        records[row[0]][field_info["name"][row[1]]] = row[2]
        field_type["string"][field_info["name"][row[1]]] = True

    for f in exclude_field_list:
        if f in field_type["string"]:
            field_type["string"].pop(f)

    sql = config_json["queries"]["query_42"].replace("QVALUE1", str(dataset_id)).replace("QVALUE2", field_value)
    cur = db.session.execute(text(sql))

    for row in cur.fetchall():
        if row[0] not in records:
            records[row[0]] = {}
        value = float(row[2]) if field_info["type"][row[1]] == "float" else int(row[2])
        records[row[0]][field_info["name"][row[1]]] = value
        field_type["numeric"][field_info["name"][row[1]]] = True

    type_list = ["string"] * len(field_type["string"]) + ["number"] * len(field_type["numeric"])
    data_frame1 = [list(field_type["string"].keys()) + list(field_type["numeric"].keys()), type_list]
    data_frame2 = [["Primary ID"] + list(field_type["string"].keys()) + list(field_type["numeric"].keys())]

    for record_id in records:
        for f in exclude_field_list:
            if f in field_type["string"]:
                records[record_id].pop(f)
        if "expressionScore" in records[record_id]:
            records[record_id]["expressionScore"] = round(records[record_id]["expressionScore"], 5)
        row1, row2 = [], []
        for f in list(field_type["string"].keys()) + list(field_type["numeric"].keys()):
            val = records[record_id][f]
            if f == "pmid":
                url = config_json[config_json["server"]]["rootinfo"]["pubmedurl"] + val
                link = f"<a href={url}>{val}<a>"
                row1.append(link)
            else:
                row1.append(val)
            row2.append(val)
        data_frame1.append(row1)
        data_frame2.append([field_value] + row2)

    return data_frame1, data_frame2


def filter_bgee_table(server_json, do_list, data_frame_one, data_frame_two):
    uberonid2name = {}
    with open(os.path.join(server_json["pathinfo"]["htmlpath"], "csv", "uberonid2name.csv"), "r") as fr:
        for line in fr:
            parts = line.strip().split(",")
            uberonid2name[parts[0]] = parts[1]

    uberon_list = []
    with open(os.path.join(server_json["pathinfo"]["htmlpath"], "csv", "doid2uberonid-mapping.csv"), "r") as fr:
        for line in fr:
            parts = line.strip().split(",")
            do_id = parts[0].strip()
            uberon_id = parts[1].strip()
            if do_id in do_list:
                uberon_list.append(uberon_id)

    uberon_list = sorted(set(uberon_list))

    data_frame_one_new = [
        ['expressionCall', 'uberonAnatomyId', 'uberonAnatomyName', 'uberonDevelopmentId', 'sex', 'expressionScore'],
        ['string', 'string', 'string', 'string', 'string', 'number']
    ]
    data_frame_two_new = [
        ['uniprotAc', 'expressionCall', 'uberonAnatomyId', 'uberonAnatomyName', 'uberonDevelopmentId', 'sex', 'expressionScore'],
    ]

    if len(data_frame_two) < 3:
        return data_frame_one_new, data_frame_two_new

    uniprot_ac = data_frame_two[3][0]
    for row in data_frame_one:
        if "UBERON" in row[2]:
            uberon_id = row[2].split(":")[1].strip()
            if uberon_id in uberon_list:
                new_row = [row[0], row[2], uberonid2name[uberon_id], row[1]] + row[3:]
                data_frame_one_new.append(new_row)
                new_row = [uniprot_ac, row[0], row[2], uberonid2name[uberon_id], row[1]] + row[3:]
                data_frame_two_new.append(new_row)

    return data_frame_one_new, data_frame_two_new


def get_transcript_data(in_json: dict) -> dict:
    out_json = {}

    with open("config.json", "r") as config_file:
        config_json = json.load(config_file)

    try:
        server_json = config_json[config_json["server"]]

        field_value = in_json["fieldvalue"].lower().strip()

        # Fetch feature information
        sql = config_json["queries"]["query_14"].replace("QVALUE", field_value)
        result = db.session.execute(text(sql)).fetchone()
        feature_id, feature_type, feature_name = result[0], result[1], result[2]

        # Fetch expression table data
        expression_table = []
        sql = config_json["queries"]["query_2"].replace("QVALUE", field_value)
        cur = db.session.execute(text(sql))

        for row in cur.fetchall():
            cancer_name = row[0]
            if "& DOID" in cancer_name:
                cancer_name = cancer_name.split("&")[-1]
            if len(cancer_name) > 50:
                cancer_name = cancer_name[:50] + " ..."
            obj = [cancer_name]
            for j in range(1, len(row)):
                value = row[j] if isinstance(row[j], str) else float(row[j])
                obj.append(value)
            expression_table.append(obj)

        # Generate other data as needed
        bgee_table1, bgee_table2 = get_data_set_table(config_json, field_value, 1, ["uniprotAc"])
        bgee_table1, bgee_table2 = filter_bgee_table(server_json, expression_table, bgee_table1, bgee_table2)

        textmine_table1, textmine_table2 = get_data_set_table(config_json, field_value, 6, ["uniprotAc", "geneMentioned", "isSamePatient"])

        out_json = {
            "taskStatus": 1,
            "inJson": in_json,
            "pageconf": config_json["pageconf"]["transcriptview"],
            "expressiontable": expression_table,
            "bgeetable": bgee_table1,
            "textminetable": textmine_table1,
        }

        # Add file downloads
        out_json["downloadfiles"] = []
        out_json["downloadfiles"].append(dump_csv_file(expression_table, server_json, "de-"))
        out_json["downloadfiles"].append(dump_csv_file(bgee_table2, server_json, "bgee-"))
        out_json["downloadfiles"].append(dump_csv_file(textmine_table2, server_json, "textmine-"))

        db.session.close()
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        out_json = {"taskStatus": 0, "errorMsg": "Service error! Please check the logs for details."}

    return out_json

def transcript_search(in_json: dict) -> dict:
    out_json = {}
    with open("config.json", "r") as config_file:
        config_json = json.load(config_file)
    try:
        server_json = config_json[config_json["server"]]

        qry_list = in_json.get("qrylist", [])
        qry_hash = {obj["fieldname"]: obj["fieldvalue"] for obj in qry_list}

        obj_list1 = []
        obj_list2 = []

        if qry_hash.get("searchtype") == "transcriptsearch":
            field_value = qry_hash["searchvalue1"].lower().strip()
            sql1 = config_json["queries"]["query_1"].replace("QVALUE", field_value)

            cur1 = db.session.execute(text(sql1))
            cur = db.session

            label_list = config_json["tableheaders"]["transcriptsearchresults"]["labellist"]
            type_list = config_json["tableheaders"]["transcriptsearchresults"]["typelist"]
            obj_list1 = [label_list, type_list]
            obj_list2 = [label_list]

            for row1 in cur1.fetchall():
                obj1, obj2 = [""], [""]
                for j in range(1, len(row1)):
                    obj1.append(row1[j])
                    obj2.append(row1[j])

                sql = config_json["queries"]["query_11"].replace("QVALUE", str(row1[0]))
                tmp_list = []
                xref_hash = {}
                cur_result = cur.execute(text(sql)).fetchall()
                for row in cur_result:
                    key = row[0].lower()
                    xref_hash[key] = row[1]
                    tmp_list.append(f"{row[0]}:{row[1]}")
                obj1.append("<br>".join(tmp_list))
                obj2.append(";".join(tmp_list))

                sql = config_json["queries"]["query_12"].replace("QVALUE", str(row1[0]))
                tmp_list = []
                cur_result = cur.execute(text(sql)).fetchall()
                for row in cur_result:
                    tmp_list.append(row[0])
                obj1.append("<br>".join(tmp_list))
                obj2.append(";".join(tmp_list))

                sql = config_json["queries"]["query_13"].replace("QVALUE", str(row1[0]))
                tmp_list = []
                cur_result = cur.execute(text(sql)).fetchall()
                for row in cur_result:
                    tmp_list.append(row[0])
                obj1.append("; ".join(tmp_list))
                obj2.append(";".join(tmp_list))

                primary_ac = xref_hash.get("uniprotkb", xref_hash.get("hgnc", ""))
                obj1[0] = f'<a href="{server_json["rootinfo"]["transcriptviewurl"]}{primary_ac}">{primary_ac}</a>'
                obj2[0] = primary_ac
                obj_list1.append(obj1)
                obj_list2.append(obj2)

        out_json = {
            "taskStatus": 1,
            "inJson": in_json,
            "searchresults": obj_list1,
        }

        time_stamp = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H-%M-%S')
        out_json["pageconf"] = config_json["pageconf"]["searchresults"]

        output_file = os.path.join(server_json["pathinfo"]["tmppath"], f"bioxpress-searchresults-{time_stamp}.csv")
        out_json["downloadfiles"] = [f"bioxpress-searchresults-{time_stamp}.csv"]

        with open(output_file, "w") as fw:
            for row in obj_list2:
                fw.write(",".join(map(str, row)) + "\n")

        os.chmod(output_file, 0o777)

    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        log_file = f"/tmp/{config_json['module'].lower()}-error.log"
        with open(log_file, "w") as fw:
            fw.write(f"{traceback.format_exc()}")
        out_json = {"taskStatus": 0, "errorMsg": f"Service error! Please see {log_file} for details."}

    return out_json
