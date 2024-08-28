import traceback
from typing import Any
import datetime
from flask import current_app as app
from sqlalchemy import text
import time
from bioxpress.db import db
import subprocess


def search_cancer(in_json: dict):

    out_json = {}
    config_json = app.config["CONFIG_JSON"]

    try:
        qryHash = {}
        for obj in in_json["qrylist"]:
            qryHash[obj["fieldname"]] = obj["fieldvalue"]
        if "cancerid" not in qryHash:
            return {"taskStatus": 0, "errorMsg": "Missing cancerid fieldname"}
        if "featuretype" not in qryHash:
            return {"taskStatus": 0, "errorMsg": "Missing featuretype fieldname"}
        if "dedirection" not in qryHash:
            return {"taskStatus": 0, "errorMsg": "Missing dedirection fieldname"}
        if "cutoff" not in qryHash:
            return {"taskStatus": 0, "errorMsg": "Missing cutoff fieldname"}

        # dataSource = ""
        sql = (
            text(config_json["queries"]["query_31"])
            if qryHash["dedirection"] != "both"
            else text(config_json["queries"]["query_32"])
        )
        sql = sql.params(
            qvalue1=qryHash["cancerid"],
            qvalue2=qryHash["featuretype"],
            qvalue3=qryHash["dedirection"],
            qvalue4=qryHash["cutoff"],
        )

        if qryHash["cutoff"].find("|") != -1:
            sql = text(config_json["queries"]["query_33"])
            sql = sql.params(
                qvalue1=qryHash["cancerid"],
                qvalue2=qryHash["featuretype"],
                qvalue3=qryHash["dedirection"],
                qvalue4=qryHash["cutoff"].split("|")[0],
                qvalue5=qryHash["cutoff"].split("|")[1],
            )

        labellist = config_json["tableheaders"]["cancerview"]["labellist"]
        typelist = config_json["tableheaders"]["cancerview"]["typelist"]
        # csvBuffer = ",".join(labellist) + "\n"
        objList1 = [labellist, typelist]
        objList2 = [labellist]
        plotData1, plotAnn1 = [], []
        plotData1.append(
            [
                "null",
                config_json["pageconf"]["cancerview"]["plotylegend1_y1"],
                config_json["pageconf"]["cancerview"]["plotylegend1_y2"],
            ]
        )

        countHash0, countHash1, countHash2, trendHash0 = {}, {}, {}, {}
        cursor = db.session.execute(sql)
        for row in cursor.fetchall():
            obj1: list[Any] = [""]
            obj2 = [""]
            for j in range(0, len(row)):
                value = row[j] if typelist[j + 1] == "string" else float(row[j])
                obj1.append(value)
                obj2.append(row[j])

            sql = text(config_json["queries"]["query_15"]).params(qvalue=str(row[0]))
            cursor1 = db.session.execute(sql)
            xrefHash = {}
            for r in cursor1.fetchall():
                key = r[0].lower()
                xrefHash[key] = r[1]
            obj1[0] = xrefHash["uniprotkb"]
            obj2[0] = xrefHash["uniprotkb"]

            objList1.append(obj1)
            objList2.append(obj2)
            if row[1].strip() != "-":
                featureName = row[0]
                ratioN = round(float(row[1].split("(")[0].split("/")[0]), 2)  # )
                ratioD = round(float(row[1].split("(")[0].split("/")[1]), 2)  # )
                col1 = round(float(ratioN * 100 / ratioD), 2)
                col2 = round(float(float(row[3]) * 100 / ratioD), 2)
                countHash1[featureName] = col1
                countHash0[featureName] = col2

                if qryHash["featuretype"] == "mrna":
                    countHash2[featureName] = col2
                else:
                    countHash2[featureName] = col1
                if row[7].lower() == "up":
                    trendHash0[featureName] = "+"
                    countHash1[featureName] = col1
                    countHash0[featureName] = col2
                elif row[7].lower() == "down":
                    trendHash0[featureName] = "-"
                    countHash1[featureName] = col1
                    countHash0[featureName] = col2

        itemCount = 0
        for t in sorted(countHash2.items(), key=lambda x: x[1], reverse=True):
            featureName = t[0]
            plotData1.append(
                [featureName, countHash1[featureName], countHash0[featureName]]
            )
            plotAnn1.append([trendHash0[featureName], trendHash0[featureName]])
            if itemCount > 20:
                break
            itemCount += 1

        for i in range(0, len(objList1)):
            objList1[i] = objList1[i][0:3] + objList1[i][4:]
        for i in range(0, len(objList2)):
            objList2[i] = objList2[i][0:3] + objList2[i][4:]

        out_json = {
            "taskStatus": 1,
            "inJson": in_json,
            "pageconf": config_json["pageconf"]["cancerview"],
            "searchresults": objList1,
            "plotdata1": plotData1,
            "plotxlabel1": config_json["pageconf"]["cancerview"]["plotxlabel_1"],
            "plotylabel1": config_json["pageconf"]["cancerview"]["plotylabel_1"],
            "plotann1": plotAnn1,
        }

        timeStamp = datetime.datetime.fromtimestamp(time.time()).strftime(
            "%Y-%m-%d-%H-%M-%S"
        )
        outputFile = (
            config_json["tmppath"] + "/bioxpress-searchresults-" + timeStamp + ".csv"
        )

        out_json["downloadfiles"] = ["bioxpress-searchresults-" + timeStamp + ".csv"]
        # errorMsg = "Could not write out CSV file " + outputFile

        FW = open(outputFile, "w")
        for i in range(0, len(objList2)):
            for j in range(0, len(objList2[i])):
                objList2[i][j] = str(objList2[i][j])
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
