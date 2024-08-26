import os,sys
import MySQLdb
import string
import commands
from optparse import OptionParser
import glob
import json


sys.path.append('../lib/')
import csvutil



__version__="1.0"
__status__ = "Dev"




###############################
def main():

    config_string = open("conf/config.json", "r").read()
    config_obj = json.loads(config_string)
    db_obj = config_obj["dbinfo"]

    dbh = MySQLdb.connect(
        host = db_obj["host"], 
        user = db_obj["userid"],
        passwd = db_obj["password"],
        db = db_obj["dbname"]
    )



    cur = dbh.cursor()
    try:
      
        #First empty the table
        sql = "delete from biox_dataset_records"
        cur.execute(sql)
        sql = "delete from biox_dataset_numericvalues"
        cur.execute(sql)
        sql = "delete from biox_dataset_stringvalues"
        cur.execute(sql)

        #Reset auto increment
        sql = "ALTER TABLE biox_dataset_records AUTO_INCREMENT = 1"
        cur.execute(sql)
        
        sql = "ALTER TABLE biox_dataset_numericvalues AUTO_INCREMENT = 1"
        cur.execute(sql)
        
        sql = "ALTER TABLE biox_dataset_stringvalues AUTO_INCREMENT = 1"
        cur.execute(sql)
        
        dbh.commit()
       
        with open("logs/dataset_records.log", "w") as FW:
            FW.write("started loading table\n")

        load_count = 0
        for ds_file in config_obj["datasetinfo"]:
            src = ds_file.split("/")[-2]
            if src in ["bgee", "dexter"]:
                file_name = ds_file.split("/")[-1]
                sql = "SELECT id FROM biox_datasets WHERE name = '%s'" % (file_name)
                cur.execute(sql)
                row = cur.fetchone()
                dataset_id = row[0]
                with open(ds_file, "r") as FR:
                    lcount = 0
                    for line in FR:
                        lcount += 1
                        row = line.strip().split("\t")
                        if lcount == 1:
                            f_list = row
                        else:
                            main_id = row[0]
                            sql = "INSERT INTO biox_dataset_records (datasetId,mainId) VALUES "
                            sql += "(%s,'%s')" % (dataset_id, main_id)
                            cur.execute(sql)
                            sql = "SELECT LAST_INSERT_ID()"
                            cur.execute(sql)
                            r = cur.fetchone()
                            record_id = r[0]
                            
                            list_one = config_obj["datasetinfo"][ds_file]["string"]
                            list_two = config_obj["datasetinfo"][ds_file]["numeric"]
                            for field in list_one + list_two:
                                field_type = "string" if field in list_one else "numeric"
                                sql = "SELECT id FROM biox_dataset_fields WHERE "
                                sql += "datasetId = %s AND name = '%s'" % (dataset_id, field)
                                cur.execute(sql)
                                r = cur.fetchone()
                                field_id = r[0]
                                field_value = row[f_list.index(field)].replace("'", "`")
                                sql = "INSERT INTO biox_dataset_%svalues " % (field_type)
                                sql += "(recordId,fieldId,value) VALUES "
                                if field_type == "string":
                                    sql += " (%s,%s,'%s')" % (record_id, field_id, field_value)
                                else:
                                    sql += " (%s,%s,%s)" % (record_id, field_id, field_value) 
                                cur.execute(sql)
                            if load_count%1000 == 0:
                                with open("logs/dataset_records.log", "a") as FA:
                                    FA.write("loaded %s records of %s.\n" % (load_count,file_name))
                            load_count += 1
                dbh.commit()
    except Exception, e:
        print e
        #print "there was some problem with the sqls"
        dbh.rollback()
    
    dbh.close()




if __name__ == '__main__':
	main()


