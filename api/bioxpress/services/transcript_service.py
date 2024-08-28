import os
import datetime
import time
from flask import current_app as app
from sqlalchemy import text
from bioxpress.db import db


def dump_csv_file(data_frame, config_json, file_prefix):
    time_stamp = datetime.datetime.fromtimestamp(time.time()).strftime(
        "%Y-%m-%d-%H-%M-%S"
    )
    output_file = os.path.join(config_json["tmppath"], f"{file_prefix}{time_stamp}.csv")

    with open(output_file, "w") as fw:
        for row in data_frame:
            fw.write(",".join(map(str, row)) + "\n")

    os.chmod(output_file, 0o777)

    return f"{file_prefix}{time_stamp}.csv"


def get_data_set_table(config_json, field_value, dataset_id, exclude_field_list):
    cur = db.session.execute(
        text(config_json["queries"]["query_4"]).params(qvalue=str(dataset_id))
    )
    field_info = {"name": {}, "type": {}}
    field_type = {"string": {}, "numeric": {}}

    for row in cur.fetchall():
        field_info["name"][row[0]] = row[1]
        field_info["type"][row[0]] = row[2]

    records = {}
    sql = text(config_json["queries"]["query_41"]).params(
        qvalue1=str(dataset_id), qvalue2=field_value
    )
    cur = db.session.execute(sql)

    for row in cur.fetchall():
        if row[0] not in records:
            records[row[0]] = {}
        records[row[0]][field_info["name"][row[1]]] = row[2]
        field_type["string"][field_info["name"][row[1]]] = True

    for f in exclude_field_list:
        if f in field_type["string"]:
            field_type["string"].pop(f)

    sql = text(config_json["queries"]["query_42"]).params(
        qvalue1=str(dataset_id), qvalue2=field_value
    )
    cur = db.session.execute(sql)

    for row in cur.fetchall():
        if row[0] not in records:
            records[row[0]] = {}
        value = float(row[2]) if field_info["type"][row[1]] == "float" else int(row[2])
        records[row[0]][field_info["name"][row[1]]] = value
        field_type["numeric"][field_info["name"][row[1]]] = True

    type_list = ["string"] * len(field_type["string"]) + ["number"] * len(
        field_type["numeric"]
    )
    data_frame1 = [
        list(field_type["string"].keys()) + list(field_type["numeric"].keys()),
        type_list,
    ]
    data_frame2 = [
        ["Primary ID"]
        + list(field_type["string"].keys())
        + list(field_type["numeric"].keys())
    ]

    for record_id in records:
        for f in exclude_field_list:
            if f in field_type["string"]:
                records[record_id].pop(f)
        if "expressionScore" in records[record_id]:
            records[record_id]["expressionScore"] = round(
                records[record_id]["expressionScore"], 5
            )
        row1, row2 = [], []
        for f in list(field_type["string"].keys()) + list(field_type["numeric"].keys()):
            val = records[record_id][f]
            if f == "pmid":
                url = config_json["urls"]["pubmedurl"] + val
                link = f"<a href={url}>{val}<a>"
                row1.append(link)
            else:
                row1.append(val)
            row2.append(val)
        data_frame1.append(row1)
        data_frame2.append([field_value] + row2)

    return data_frame1, data_frame2


def filter_bgee_table(config_json, do_list, data_frame_one, data_frame_two):
    uberonid2name = {}
    with open(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "csv", "uberonid2name.csv"
        ),
        "r",
    ) as fr:
        for line in fr:
            parts = line.strip().split(",")
            uberonid2name[parts[0]] = parts[1]

    uberon_list = []
    with open(
        os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "csv",
            "doid2uberonid-mapping.csv",
        ),
        "r",
    ) as fr:
        for line in fr:
            parts = line.strip().split(",")
            do_id = parts[0].strip()
            uberon_id = parts[1].strip()
            if do_id in do_list:
                uberon_list.append(uberon_id)

    uberon_list = sorted(set(uberon_list))

    data_frame_one_new = [
        [
            "expressionCall",
            "uberonAnatomyId",
            "uberonAnatomyName",
            "uberonDevelopmentId",
            "sex",
            "expressionScore",
        ],
        ["string", "string", "string", "string", "string", "number"],
    ]
    data_frame_two_new = [
        [
            "uniprotAc",
            "expressionCall",
            "uberonAnatomyId",
            "uberonAnatomyName",
            "uberonDevelopmentId",
            "sex",
            "expressionScore",
        ],
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
                new_row = [
                    uniprot_ac,
                    row[0],
                    row[2],
                    uberonid2name[uberon_id],
                    row[1],
                ] + row[3:]
                data_frame_two_new.append(new_row)

    return data_frame_one_new, data_frame_two_new


def get_transcript_data(in_json: dict) -> dict:

    out_json = {}
    config_json = app.config["CONFIG_JSON"]

    try:
        field_value = in_json["fieldvalue"].lower().strip()

        # Fetch feature information
        sql = text(config_json["queries"]["query_14"]).params(qvalue=field_value)
        result = db.session.execute(sql).fetchone()
        # feature_id, feature_type, feature_name = result[0], result[1], result[2]

        # Fetch expression table data
        expression_table = []
        sql = text(config_json["queries"]["query_2"]).params(qvalue=field_value)
        cur = db.session.execute(sql)

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
        bgee_table1, bgee_table2 = get_data_set_table(
            config_json, field_value, 1, ["uniprotAc"]
        )
        bgee_table1, bgee_table2 = filter_bgee_table(
            config_json, expression_table, bgee_table1, bgee_table2
        )

        textmine_table1, textmine_table2 = get_data_set_table(
            config_json, field_value, 6, ["uniprotAc", "geneMentioned", "isSamePatient"]
        )

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
        out_json["downloadfiles"].append(
            dump_csv_file(expression_table, config_json, "de-")
        )
        out_json["downloadfiles"].append(
            dump_csv_file(bgee_table2, config_json, "bgee-")
        )
        out_json["downloadfiles"].append(
            dump_csv_file(textmine_table2, config_json, "textmine-")
        )

        db.session.close()
    except Exception as e:
        app.logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        out_json = {
            "taskStatus": 0,
            "errorMsg": "Service error! Please check the logs for details.",
        }

    return out_json
