import os,sys
import MySQLdb
import string
import commands
from optparse import OptionParser
import glob
import json
import numpy

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
        
        #First empty the table
        sql = "delete from biox_boxplot"
        cur.execute(sql)
        
        #Reset auto increment
        sql = "ALTER TABLE biox_boxplot AUTO_INCREMENT = 1"
        cur.execute(sql)
        dbh.commit()

        #Create a dictionary to link the featureID column (auto-increment) to the featureName column (defined as "gene_name" in the source data) in the sql table biox_feature 
        genename2featureid = {}
        sql = "SELECT featureId, featureName FROM biox_feature"
        cur.execute(sql)
        for row in cur.fetchall():
            feature_id = row[0]
            gene_name = row[1]
            genename2featureid[gene_name] = feature_id
        #print "Contents of genename2featureid:"
        #print (json.dumps(genename2featureid, indent = 4))

        #Create a dictionary to link the sampleId column (auto-increment) to the sampleName column (definied as "study_id" in the data source file) in the sql table biox_tissue
        samplename2sampleid = {}
        sql = "SELECT sampleId, sampleName FROM biox_sample"
        cur.execute(sql)
        for row in cur.fetchall():
            sample_id = row[0]
            sample_name = row[1]
            samplename2sampleid[sample_name] = sample_id
        #print "Contents of samplename2sampleid:"
        #print (json.dumps(samplename2sampleid, indent = 4))

        #Create a dictionary to link the id column (auto-increment) to the doName column (definied as "doname" in the data source file) in the sql table biox_cancer
        doid2cancerid = {}
        sql = "SELECT id, doId FROM biox_cancer"
        cur.execute(sql)
        for row in cur.fetchall():
            cancer_id = row[0]
            doid = row[1]
            doid2cancerid[doid] = cancer_id

        #print "Contents of doid2cancerid:"
        #print (json.dumps(doid2cancerid, indent = 4))

        #We listed the headings/table structure for each source data file in the config json.
        #Set those headings to the specific source data file.
        #Indicate which csv file to load into data_frame 
        
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
            log2fc = row[f_list.index("log2fc")]
            pvalue = row[f_list.index("pvalue")]
            adjpvalue = row[f_list.index("adjpvalue")]
            significance = row[f_list.index("significance")]
            direction = row[f_list.index("direction")]
            subjects_up = row[f_list.index("subjects_up")]
            subjects_down = row[f_list.index("subjects_down")]
            subjects_nochange = row[f_list.index("subjects_nochange")]
            subjects_total = row[f_list.index("subjects_total")]
            data_source = row[f_list.index("data_source")]
            study_id = row[f_list.index("study_id")]
            sample_name = study_id.split("-")[-1]
            pmid = row[f_list.index("pmid")]
            doid = row[f_list.index("doid")]
            doname = row[f_list.index("doname")]
            uberon_id = row[f_list.index("uberon_id")]
            numpy_array = numpy.array(data_frame)
            min_value = min(numpy_array)
            max_value = max(numpy_array)
            25th_percentile = numpy.percentile(numpy_array, 25)
            50th_percentile = numpy.percentile(numpy_array, 50)
            75th_percentile = numpy.percentile(numpy_array, 75)
            frequency = 
	    if gene_name not in genename2featureid:
	        continue
	    feature_id = genename2featureid[gene_name]
            sample_id = samplename2sampleid[sample_name]          
            cancer_id = doid2cancerid[doid]
            if gene_name == "KRAS":
                print study_id,doid,feature_id,sample_id, cancer_id, subjects_up,subjects_down,subjects_total
            sql = "INSERT INTO biox_level (featureId,sampleId,sigFlag,deDirection,dataSource,pmid,cancerId,subjectsUp,subjectsDown,subjectsTotal,pValue,adjPvalue,logFc) VALUES " 
            sql += "(%s,%s,'%s','%s','%s','%s',%s,%s,%s,%s,%s,%s,%s)" % (feature_id,sample_id,significance,direction,data_source,pmid,cancer_id,subjects_up,subjects_down,subjects_total,pvalue,adjpvalue,log2fc)
            #print "%s, %s"  % (load_count, sql)
	    cur.execute(sql)
            load_count += 1
        dbh.commit()
        print "Finished loading %s rows" % (load_count)
    except Exception, e:
        print e
        dbh.rollback()
    
    dbh.close()




if __name__ == '__main__':
	main()


