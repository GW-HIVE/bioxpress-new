import os
import datetime
import time
from flask import current_app as app
from pprint import pprint
from sqlalchemy import text
from bioxpress.db import db
import math
import traceback
import subprocess


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
        result = db.session.execute(sql)
        row = result.fetchone()
        if row is None:
            sql = text(
                "SELECT xrefId from biox_xref where xrefSrc = 'UniProtKB' AND featureId in (SELECT featureId FROM biox_feature WHERE lower(featureName) = lower(:qvalue))"
            ).params(qvalue=field_value)
            result = db.session.execute(sql)
            row = result.fetchone()
            if row is None:
                return {
                    "errorMsg": "No results were found",
                    "inJson": {"fieldvalue": field_value},
                    "taskStatus": 0,
                }
            protein_accession = row[0]
            sql = text(config_json["queries"]["query_14"]).params(
                qvalue=protein_accession
            )
            result = db.session.execute(sql)
            row = result.fetchone()
            if row is None:
                return {
                    "errorMsg": "No results were found",
                    "inJson": {"fieldvalue": field_value},
                    "taskStatus": 0,
                }
            field_value = protein_accession

        feature_id, feature_type, feature_name = row[0], row[1], row[2]

        # Fetch expression table data
        sql = text(config_json["queries"]["query_2"]).params(qvalue=field_value)
        cur = db.session.execute(sql)

        labelList = config_json["tableheaders"]["transcriptview"]["labellist"]
        typeList = config_json["tableheaders"]["transcriptview"]["typelist"]
        expressionTable1 = [labelList, typeList]

        plotData1: list = []
        plotData2: list = []
        plotData3: list = []
        plotData1.append(
            [
                "null",
                config_json["pageconf"]["transcriptview"]["plotylegend1_y1"],
                config_json["pageconf"]["transcriptview"]["plotylegend1_y2"],
            ]
        )
        plotData2.append(
            [
                "null",
                config_json["pageconf"]["transcriptview"]["plotylegend2_y1"],
                config_json["pageconf"]["transcriptview"]["plotylegend2_y2"],
            ]
        )
        plotAnn2: list = []

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
            if row[1].strip() != "-":

                ratioN = round(float(row[1].split("(")[0].split("/")[0]), 2)  # )
                ratioD = round(float(row[1].split("(")[0].split("/")[1]), 2)  # )

                if ratioD < 10:
                    continue

                if row[-1].lower() == "up":
                    plotData1.append([cancer_name, ratioN, ratioD - ratioN])
                else:
                    plotData1.append([cancer_name, ratioD - ratioN, ratioN])
                y1 = round(float(ratioN * 100 / ratioD), 2)
                y2 = round(float(float(row[2]) * 100 / ratioD), 2)
                plotData2.append([cancer_name, y1, y2])
                ann = "+" if row[-1].lower() == "up" else "-"
                plotAnn2.append([ann, ann])
                expressionTable1.append(obj)

        sql = text(
            config_json["queries"]["query_21"]
            if feature_type == "mrna"
            else config_json["queries"]["query_23"]
        ).params(qvalue=field_value)
        cur = db.session.execute(sql)

        for row in cur.fetchall():
            x = row[0]
            y1 = math.log(row[1]) / math.log(2) if row[1] != 0.0 else 0
            y2 = math.log(row[2]) / math.log(2) if row[2] != 0.0 else 0
            y3 = math.log(row[3]) / math.log(2) if row[3] != 0.0 else 0
            y4 = math.log(row[4]) / math.log(2) if row[4] != 0.0 else 0
            y5 = math.log(row[5]) / math.log(2) if row[5] != 0.0 else 0
            plotData3.append([x, y1, y2, y3, y4, y5])

        do_list = []
        for row in expressionTable1:
            parts = row[0].split("/")[0].split(":")
            if parts[0] == "DOID":
                do_list.append(parts[1].strip())
        do_list = sorted(set(do_list))

        # Generate other data as needed
        bgee_table1, bgee_table2 = get_data_set_table(
            config_json, field_value, 1, ["uniprotAc"]
        )
        bgee_table1, bgee_table2 = filter_bgee_table(
            config_json, do_list, bgee_table1, bgee_table2
        )

        textmine_table1, textmine_table2 = get_data_set_table(
            config_json, field_value, 6, ["uniprotAc", "geneMentioned", "isSamePatient"]
        )

        for i in range(0, len(expressionTable1)):
            expressionTable1[i] = expressionTable1[i][:2] + expressionTable1[i][3:]

        if feature_type == "mirna":
            plotData2 = []

        out_json = {
            "taskStatus": 1,
            "inJson": in_json,
            "pageconf": config_json["pageconf"]["transcriptview"],
            "expressiontable": expressionTable1,
            "bgeetable": bgee_table1,
            "textminetable": textmine_table1,
            "plotdata1": plotData1,
            "plotdata2": plotData2,
            "plotdata3": plotData3,
            "plotxlabel1": config_json["pageconf"]["transcriptview"]["plotxlabel_1"],
            "plotxlabel2": config_json["pageconf"]["transcriptview"]["plotxlabel_2"],
            "plotxlabel3": config_json["pageconf"]["transcriptview"]["plotxlabel_3"],
            "plotylabel1": config_json["pageconf"]["transcriptview"]["plotylabel_1"],
            "plotylabel2": config_json["pageconf"]["transcriptview"]["plotylabel_2"],
            "plotylabel3": config_json["pageconf"]["transcriptview"]["plotylabel_3"],
            "plotann2": plotAnn2,
        }

        query = in_json["fieldvalue"].upper()
        for key in out_json["pageconf"]:
            out_json["pageconf"][key] = out_json["pageconf"][key].replace(
                "QVALUE", query
            )
            out_json["pageconf"][key] = out_json["pageconf"][key].replace(
                "SYMBOL", feature_name
            )
            out_json["pageconf"][key] = out_json["pageconf"][key].replace(
                "BIOMUTAURL", config_json["urls"]["biomutaurl"] + query
            )

        expressionTable2: list = []
        row = ["Primary ID"] + expressionTable1[0]
        expressionTable2.append(row)
        for i in range(2, len(expressionTable1)):
            row = [field_value] + expressionTable1[i]
            expressionTable2.append(row)

        out_json["downloadfiles"] = []
        out_json["downloadfiles"].append(
            dump_csv_file(expressionTable2, config_json, "de-")
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


def transcript_search(in_json: dict) -> dict:

    out_json = {}
    print("IN_JSON for transcript search:")
    pprint(in_json, indent=2)
    config_json = app.config["CONFIG_JSON"]
    # error_msg = ""

    try:
        # seen = {}
        qry_hash = {}
        for obj in in_json["qrylist"]:
            qry_hash[obj["fieldname"]] = obj["field_value"]

        objList1 = []
        objList2 = []

        if qry_hash["searchtype"] == "transcriptsearch":
            field_value = qry_hash["searchvalue1"].lower().strip()
            sql1 = text(config_json["queries"]["query_1"]).params(qvalue=field_value)

            labellist = config_json["tableheaders"]["transcriptsearchresults"][
                "labellist"
            ]
            typelist = config_json["tableheaders"]["transcriptsearchresults"][
                "typelist"
            ]
            objList1 = [labellist, typelist]
            objList2 = [labellist]
            # featureIdList = []

            cursor1 = db.session.execute(sql1)
            for row1 in cursor1.fetchall():
                obj1, obj2 = [""], [""]
                for j in range(1, len(row1)):
                    obj1.append(row1[j])
                    obj2.append(row1[j])
                sql = text(config_json["queries"]["query_11"]).params(
                    qvalue=str(row1[0])
                )
                cursor = db.session.execute(sql)
                tmpList = []
                xrefHash = {}
                for row in cursor.fetchall():
                    key = row[0].lower()
                    xrefHash[key] = row[1]
                    tmpList.append(row[0] + ":" + row[1])
                obj1.append("<br>".join(tmpList))
                obj2.append(";".join(tmpList))

                sql = text(config_json["queries"]["query_12"]).params(
                    qvalue=str(row1[0])
                )
                cursor = db.session.execute(sql)
                tmpList = []
                for row in cursor.fetchall():
                    tmpList.append(row[0])
                obj1.append("<br>".join(tmpList))
                obj2.append(";".join(tmpList))
                sql = text(config_json["queries"]["query_13"]).params(
                    qvalue=str(row1[0])
                )
                cursor = db.session.execute(sql)
                tmpList = []
                for row in cursor.fetchall():
                    tmpList.append(row[0])
                obj1.append("; ".join(tmpList))
                obj2.append(";".join(tmpList))

                primaryAc = (
                    xrefHash["uniprotkb"]
                    if "uniprotkb" in xrefHash
                    else xrefHash["hgnc"]
                )
                obj1[0] = (
                    '<a href"'
                    + config_json["urls"]["transcriptviewurl"]
                    + primaryAc
                    + '">'
                    + primaryAc
                    + "</a>"
                )
                obj2[0] = primaryAc
                objList1.append(obj1)
                objList2.append(obj2)

        out_json = {"taskStatus": 1, "inJson": in_json, "searchresults": objList1}
        timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime(
            "%Y-%m-%d-%H-%M-%S"
        )
        out_json["pageconf"] = config_json["pageconf"]["searchresults"]

        outputFile = (
            config_json["tmppath"] + "/bioxpress-searchresults-" + timeStamp + ".csv"
        )
        out_json["downloadfiles"] = ["bioxpress-searchresults-" + timeStamp + ".csv"]
        # error_msg = "Could not write out CSV file " + outputFile

        FW = open(outputFile, "w")
        for i in range(0, len(objList2)):
            FW.write("%s\n" % (",".join(objList2[i])))
        FW.close()
        cmd = "chmod 777 " + outputFile
        subprocess.getoutput(cmd)

        return out_json

    except Exception as e:
        logFile = "/tmp/%s-error.log" % (config_json["module"].lower())
        with open(logFile, "w") as FW:
            FW.write("%s" % (traceback.format_exc()))
        msg = "Service error! Please see %s-error.log for details.<br><br>" % (
            config_json["project"].lower()
        )
        return {"taskStatus": 0, "errorMsg": msg}
