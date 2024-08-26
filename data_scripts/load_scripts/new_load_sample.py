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
        sql = "delete from biox_sample"
        cur.execute(sql)
        
        #Reset auto increment
        sql = "ALTER TABLE biox_sample AUTO_INCREMENT = 1"
        cur.execute(sql)
        dbh.commit()

        #Create a dictionary to link the tissueId column (auto-increment) in biox_tissue to the                   ##tissueName column (definied as "uberon_id" in the data source file)
        tissuename2tissueid = {}
        sql = "SELECT tissueId, tissueName FROM biox_tissue"
        cur.execute(sql)
        for row in cur.fetchall():
            tissue_id = row[0]
            tissue_name = row[1]
            tissuename2tissueid[tissue_name] = tissue_id
        print "Contents of tissuename2tissueid:"
        print (json.dumps(tissuename2tissueid, indent = 4))

 
        #We listed the headings/table structure for each source data file in the config json.
        #Set those headings to the specific source data file. 
        data_frame = {}
        sep = "\",\""
        fields = config_obj["datasetinfo"][in_file]["string"]
        csvutil.load_large_sheet(data_frame, in_file, fields, sep)
        
        f_list = data_frame["fields"]
        load_count = 0
        for row in data_frame["data"]:
            study_id = row[f_list.index("study_id")]
            do_id = row[f_list.index("do_id")]
            do_name = row[f_list.index("do_name")]
            tissue_name = "UBERON:%s" % (row[f_list.index("uberon_id")])
            uberon_name = row[f_list.index("uberon_name")]
            tissue_id = tissuename2tissueid[tissue_name]
            
            sql = "INSERT INTO biox_sample (sampleName,sampleSynonym,tissueId) VALUES " 
            sql += "('%s','%s & DOID:%s','%s')" % (study_id,do_name,do_id,tissue_id)
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


