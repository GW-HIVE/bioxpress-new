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


    in_file = "generated/bioxpress-final.de.csv"
    #in_file = "tmp/toy.csv"

    cur = dbh.cursor()
    try:
        
        genename2featureid = {}
        sql = "SELECT featureId, featureName FROM biox_feature"
        cur.execute(sql)
        for row in cur.fetchall():
            feature_id = row[0]
            gene_name = row[1]
            genename2featureid[gene_name] = feature_id
        
        #Set those headings to the specific source data file. 
        data_frame = {}
        sep = "\",\""
        fields = config_obj["datasetinfo"][in_file]["string"]
        csvutil.load_large_sheet(data_frame, in_file, fields, sep)        
   
        f_list = data_frame["fields"]
        load_count = 0
        for row in data_frame["data"]:
	    uniprot_ac = row[f_list.index("uniprot_ac")]
            refseq_ac = row[f_list.index("refseq_ac")]
            gene_name = row[f_list.index("gene_name")]
	    if gene_name not in genename2featureid:
	        print gene_name
                continue
            load_count += 1
    except Exception, e:
        print e
    
    dbh.close()




if __name__ == '__main__':
	main()


