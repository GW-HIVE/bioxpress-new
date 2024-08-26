#!/usr/bin/python
import os,sys
import string
import cgi,csv
import commands
import json
import util
import searchQueryFormatting as sqf
import MySQLdb
from optparse import OptionParser

__version__="1.0"

#############################################
def isNumeric(value):
	try:
		float(value)
		return True
	except ValueError:
		return False


#############################################
def main():

	usage = "\n%prog  [options]"
	parser = OptionParser(usage,version="%prog " + __version__)
	parser.add_option("-s","--species",action="store",dest="species",help="human/mouse")


	(options,args) = parser.parse_args()
	for file in ([options.species]):
		if not (file):
			parser.print_help()
			sys.exit(0)
	

	PHASH = {}

	taxname2datasetid ={"human":1, "mouse":3}

	uberonid2name = {}
	with open("/data/Knowledgebases/BioMuta/uberonid2name.csv", "r") as FR:
                for line in FR:
			parts = line.strip().split(",")
                        uberonid2name[parts[0]] = parts[1]

	uberonid2doid = {}
	with open("/data/Knowledgebases/BioMuta/doid2uberonid-mapping.csv", "r") as FR:
		for line in FR:
			parts = line.strip().split(",")
			uberonid2doid[parts[1]] = parts[0]


	util.LoadParams("./conf/database.txt", PHASH)
       	DBH = MySQLdb.connect(host = PHASH['DBHOST'], user = PHASH['DBUSERID'], 
			passwd = PHASH['DBPASSWORD'], db = PHASH['DBNAME'])
	cur = DBH.cursor()


	dataset_id = taxname2datasetid[options.species]

	fieldid2name = {}
	sql = "SELECT id, name FROM biox_dataset_fields WHERE datasetId = %s " % (dataset_id)
	cur.execute(sql)
        for row in cur.fetchall():
                fieldid2name[row[0]] = row[1]
	

	data_grid = {}
	seen = {}

	sql = "SELECT A.id, A.mainId, B.fieldId, B.value FROM biox_dataset_records A, biox_dataset_numericvalues B WHERE A.id = B.recordId AND A.datasetId = %s  " % (dataset_id)
	cur.execute(sql)
	for row in cur.fetchall():
		record_id = row[0]
		field_name = fieldid2name[row[2]]
		if record_id not in data_grid:
			data_grid[record_id] = {}
 
		data_grid[record_id][field_name] = row[3]
		seen[field_name] = True
	
	sql = "SELECT A.id, A.mainId, B.fieldId, B.value FROM biox_dataset_records A, biox_dataset_stringvalues B WHERE A.id = B.recordId AND A.datasetId = %s  " % (dataset_id)
        cur.execute(sql)
        for row in cur.fetchall():
                record_id = row[0]
		if record_id not in data_grid:
                        data_grid[record_id] = {}
		field_name = fieldid2name[row[2]]
		data_grid[record_id][field_name] = row[3]	
		seen[field_name] = True



	#Output
	string = "uniprotAc,expressionScore,uberonDevelopmentId,sex,uberonAnatomyId,expressionCall,uberon_name"
	field_list = string.split(",")
	print string
	for record_id in data_grid:
		uberon_id = data_grid[record_id]["uberonAnatomyId"].split(":")[1]
		if uberon_id not in uberonid2doid:
			continue
		value_list = []
		for j in xrange(0, len(field_list) -1):
			field = field_list[j]
			value = str(data_grid[record_id][field]) if field in data_grid[record_id] else ""
			value_list.append(value)
		uberon_name = uberonid2name[uberon_id] if uberon_id in uberonid2name else ""
		value_list.append(uberon_name)
		print ",".join(value_list)

	
	DBH.close()


if __name__ == '__main__':
        main()



