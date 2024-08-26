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
        parser.add_option("-o","--outfile",action="store",dest="outfile",help="Output path")

	(options,args) = parser.parse_args()
	for file in ([options.outfile]):
		if not (file):
			parser.print_help()
			sys.exit(0)


	PHASH = {}
        util.LoadParams("../biomuta/conf/database.txt", PHASH)
        DBH = MySQLdb.connect(host = PHASH['DBHOST'], user = PHASH['DBUSERID'],
                        passwd = PHASH['DBPASSWORD'], db = PHASH['DBNAME'])
        cur = DBH.cursor()
	sql = "select  A.doId, A.doName, B.uberonId from biomuta_cancer A, biomuta_do2uberon B WHERE A.doId = B.doId"
        cur.execute(sql)
        cancer_info = {}
        for row in cur.fetchall():
                if row[0] not in cancer_info:
			cancer_info[row[0]] = {"doid":row[0], "doname":row[1], "uberonid":[row[2]]}
		else:
			cancer_info[row[0]]["uberonid"].append(row[2])

	DBH.close()




	PHASH = {}
	util.LoadParams("./conf/database.txt", PHASH)
       	DBH = MySQLdb.connect(host = PHASH['DBHOST'], user = PHASH['DBUSERID'], 
			passwd = PHASH['DBPASSWORD'], db = PHASH['DBNAME'])
	cur = DBH.cursor()


	sql = "select featureId, xrefId from biox_xref where xrefSrc = 'RefSeq'"
	cur.execute(sql)
	feat2refseq = {}
	for row in cur.fetchall():
		feat2refseq[row[0]] = row[1]
	

	sql = "SELECT DISTINCT A.featureId, C.xrefId, B.featureName, A.logFc, A.pValue,A.adjPvalue,A.sigFlag,A.deDirection, A.subjectsRatio, A.dataSource, A.pmid, D.sampleId, D.sampleSynonym,E.doId FROM biox_level A, biox_feature B, biox_xref C, biox_sample D, biox_cancer E WHERE A.sampleId = D.sampleId AND A.cancerId = E.id AND A.featureId = B.featureId AND  B.featureId = C.featureId AND C.xrefSrc = 'UniProtKB'"

	cur.execute(sql)
       
	header_list = "uniprot_ac,refseq_ac,gene_name,log2fc,pvalue,adjpvalue,significance,direction,subjects_ratio,data_source,pmid,sample_name,doid,doname,parent_doid,parent_doname,uberon_id,sample_id".split(",")
 	# From biomuta_ database, get uberon_id
		
	FW = open(options.outfile, "w")
	FW.write("%s\n" % ("\"" + "\",\"".join(header_list) + "\""))

        for row in cur.fetchall():
            if row[8].strip() != "-":
                ratioN = round(float(row[8].split("(")[0].split("/")[0]), 2)
                ratioD = round(float(row[8].split("(")[0].split("/")[1]), 2)
                if ratioD < 10:
                    continue
                refseq_ac = feat2refseq[row[0]]
                parent_doid = str(row[-1])
		sample_id = str(row[11])
		values = [row[1]] + [refseq_ac] 
		for j in xrange(2, 11):
			values.append(str(row[j]))
                cancer_name = row[12]
                #Extract most specific DOID
                if cancer_name.find("& DOID") != -1:
                    cancer_name = cancer_name.split("&")[-1].strip()
                if len(cancer_name) > 50:
                    cancer_name = cancer_name[0:50] + " ..."
		doid = cancer_name.strip().split(" ")[0].split("DOID:")[1]
                values.append(cancer_name)
		values.append(doid)
                values.append(cancer_name)
                values.append(parent_doid)
		if parent_doid in cancer_info:
			values += [ cancer_info[parent_doid]["doname"],  ";".join(sorted(set(cancer_info[parent_doid]["uberonid"])))]
		else:
			values += [ "", ""]
		values += [str(sample_id)]
                FW.write("%s\n" % ("\"" + "\",\"".join(values) + "\""))

	FW.close()
	
	DBH.close()


if __name__ == '__main__':
        main()



