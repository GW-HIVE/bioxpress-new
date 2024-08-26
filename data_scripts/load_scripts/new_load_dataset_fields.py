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
        sql = "delete from biox_dataset_fields"
        cur.execute(sql)
        
        #Reset auto increment
        sql = "ALTER TABLE biox_dataset_fields AUTO_INCREMENT = 1"
        cur.execute(sql)
        dbh.commit()
      
        load_count = 0
        for f in config_obj["datasetinfo"]:
            src = f.split("/")[-2]
            if src in ["bgee", "dexter"]:
                file_name = f.split("/")[-1]
                sql = "SELECT id FROM biox_datasets WHERE name = '%s'" % (file_name)
                cur.execute(sql)
                row = cur.fetchone()
                dataset_id = row[0]        
                list_one = config_obj["datasetinfo"][f]["string"]
                list_two = config_obj["datasetinfo"][f]["numeric"]
                for field in list_one + list_two:
                    field_type = "string" if field in list_one else "numeric"
                    sql = "INSERT INTO biox_dataset_fields (datasetId,name, description,type) VALUES "
                    sql += "(%s, '%s','%s', '%s')" % (dataset_id, field, field, field_type)
                    print "%s, %s"  % (load_count, sql)
                    cur.execute(sql)
                    load_count += 1
        dbh.commit()
        print "Finshed loading %s rows" % (load_count)
    except Exception, e:
        print e
        #print "there was some problem with the sqls"
        dbh.rollback()
    
    dbh.close()




if __name__ == '__main__':
	main()


