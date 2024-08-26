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
      
        n = 60000000
        for i in xrange(1, 10000):
            n -= 100000
            sql = "delete from biox_dataset_numericvalues where id > %s " % (n)
            print sql
            cur.execute(sql)
            dbh.commit()
            
            sql = "delete from biox_dataset_stringvalues where id > %s " % (n)
            print sql
            cur.execute(sql)
            dbh.commit()

            sql = "delete from biox_dataset_records where id > %s " % (n)
            print sql 
            cur.execute(sql)
            dbh.commit()
        
        sql = "delete from biox_dataset_fields"
        cur.execute(sql)
        dbh.commit()

        sql = "delete from biox_datasets"
        cur.execute(sql)
        dbh.commit()
       
    except Exception, e:
        print e
        #print "there was some problem with the sqls"
        dbh.rollback()
    
    dbh.close()




if __name__ == '__main__':
	main()


