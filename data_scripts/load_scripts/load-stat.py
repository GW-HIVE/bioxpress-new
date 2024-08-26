import os,sys
import string
import csv
import json
from optparse import OptionParser
import MySQLdb



__version__="1.0"
__status__ = "Dev"






###############################
def main():

	usage = "\n%prog  [options]"
	parser = OptionParser(usage,version="%prog " + __version__)
	parser.add_option("-i","--configfile",action="store",dest="configfile",help="NT file")


	(options,args) = parser.parse_args()
	for file in ([options.configfile]):
		if not (file):
			parser.print_help()
			sys.exit(0)




	configJson = json.loads(open(options.configfile, "r").read())
 	DBH = MySQLdb.connect(host = configJson["dbinfo"]["host"], 
				user = configJson["dbinfo"]["userid"], 
				passwd = configJson["dbinfo"]["password"],
				db = configJson["dbinfo"]["dbname"])
        
	cur = DBH.cursor()
     
	title = "General statistics"
	json_obj = {
		"fieldtypes": ["string", "number"]
		,"fieldnames": ["", ""]
		,"dataframe": [
			 ["Number of UniProtKB accessions hit", 0]
			,["Number of differentially expressed UniProtKB accessions", 0]
			,["Number of miRNA identifiers hit", 0]
                        ,["Number of differentially expressed miRNA identifiers", 0]
			,["Disease Ontology terms mapped", 0]
                        
		]
	}

	query_list = ["q_11", "q_12",  "q_21",  "q_22", "q_41"]
	
	for i in xrange(0, len(query_list)):
		if query_list[i] == "":
			continue
		sql = configJson["queries"][query_list[i]]
		cur.execute(sql)
		row = cur.fetchone()
		json_obj["dataframe"][i][1] = int(row[0])
	

	sql = "delete from biox_stat"
	cur.execute(sql)
	sql = "ALTER TABLE biox_stat AUTO_INCREMENT = 1"
	cur.execute(sql)

	sql = "INSERT INTO biox_stat (title, jsonstring) VALUES ('%s', '%s') " % (title, json.dumps(json_obj))
	cur.execute(sql)
	
	DBH.commit()

if __name__ == '__main__':
        main()
