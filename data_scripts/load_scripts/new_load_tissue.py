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


    in_file = "generated/bioxpress-final.domap.csv"
    #in_file = "tmp/toy.csv"

    cur = dbh.cursor()
    try:
        
        #First empty the table
        sql = "delete from biox_tissue"
        cur.execute(sql)
        
        #Reset auto increment
        sql = "ALTER TABLE biox_tissue AUTO_INCREMENT = 1"
        cur.execute(sql)
        dbh.commit()
        
        data_frame = {}
        sep = "\",\""
        fields = config_obj["datasetinfo"][in_file]["string"]
        csvutil.load_large_sheet(data_frame, in_file, fields, sep)
        
        seen = {}
        f_list = data_frame["fields"]
        load_count = 0
        for row in data_frame["data"]:
            study_id = row[f_list.index("study_id")]
            do_id = row[f_list.index("do_id")]
            do_name = row[f_list.index("do_name")]
	    uberon_id = row[f_list.index("uberon_id")]
            uberon_name = row[f_list.index("uberon_name")]
            if study_id not in seen:
                sql = "INSERT INTO biox_tissue (tissueName) VALUES "
                sql += "('UBERON:%s')" % (uberon_id)
                cur.execute(sql)
                load_count += 1
                print "%s, %s"  % (load_count, sql)
                seen[study_id] = True
        dbh.commit()
        print "Finshed loading %s rows" % (load_count)

    except:
        print "there was some problem with the sqls"
        dbh.rollback()
    
    dbh.close()




if __name__ == '__main__':
	main()


