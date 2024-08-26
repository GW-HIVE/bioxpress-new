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


    in_file = "generated/bioxpress-final.xref.csv"
    #in_file = "tmp/toy.csv"

    cur = dbh.cursor()
    try:
        
        #First empty the table
        sql = "delete from biox_xref"
        cur.execute(sql)
        
        #Reset auto increment
        sql = "ALTER TABLE biox_xref AUTO_INCREMENT = 1"
        cur.execute(sql)
        dbh.commit()
       
        genename2featureid = {}
        sql = "SELECT featureId, featureName FROM biox_feature"
        cur.execute(sql)
        for row in cur.fetchall():
            feature_id = row[0]
            gene_name = row[1]
            genename2featureid[gene_name] = feature_id




        data_frame = {}
        sep = "\",\""
        fields = config_obj["datasetinfo"][in_file]["string"]
        csvutil.load_large_sheet(data_frame, in_file, fields, sep)
        
        f_list = data_frame["fields"]
        load_count = 0
        for row in data_frame["data"]:
            gene_name = row[f_list.index("gene_name")]
            xref_db = row[f_list.index("xref_db")]
            xref_id = row[f_list.index("xref_id")]
            feature_id = genename2featureid[gene_name]
            
            sql = "INSERT INTO biox_xref (xrefId,xrefSrc,featureId) VALUES " 
            sql += "('%s','%s', %s)" % (xref_id, xref_db,feature_id)
            cur.execute(sql)
            load_count += 1
            print "%s, %s"  % (load_count, sql)
        dbh.commit()
        print "Finished loading %s rows" % (load_count)
    except Exception, e:
        print e
        dbh.rollback()
    
    dbh.close()




if __name__ == '__main__':
	main()


