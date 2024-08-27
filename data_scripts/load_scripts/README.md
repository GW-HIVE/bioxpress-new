# Data Load Scripts

Files needed for complete data load:

- bioxpress-final.de.csv
- bioxpress-final.domap.csv
- bioxpress-final.xref.csv

TODO : files I think you need?

- bgee:
  - oncoMX_expression_9606.tsv
  - oncoMX_expression_10090.tsv
- dexter:
  - glycosyltransferase_textMining_tissue.txt
  - lung_cancer_all_tissue.txt
  - microRNA_textMining_tissue.txt

## Scripts

`load-stat.py`

`load_cancer.py`

`load_sample_fake.py`

`load_sample_tcga.py`

`load_subject.py`

`load_subject_fake.py`

`load_subject_tcga.py`

`new_load_boxplot.py`

`new_load_dataset_fields.py`

`new_load_dataset_records.py`

`new_load_datasets.py`

`new_load_de.py`

`new_load_doid.py`

`new_load_feature.py`

The new_load_feature.py script uploads gene feature data from a CSV file (`bioxpress-final.xref.csv`) into the `biox_feature` table. It clears the table, resets its auto-increment, and then inserts records with the `gene_name` as `featureName` and `mrna` as `featureType`. The script ensures that only unique `gene_name` entries are added.

`new_load_sample.py`

`new_load_tissue.py`

`new_load_xref.py`

The `new_load_xref.py` script is designed to load cross-reference (xref) data from a CSV file (`bioxpress-final.xref.csv`) into the `biox_xref` table within the BioXpress database. The script first deletes any existing data in the `biox_xref` table and resets the table's auto-increment counter. It then reads gene names from the `gene_name`, `xref_db`, and `xref_id` columns of the CSV file. For each gene name, the script looks up the corresponding `featureId` from the `biox_feature` table. It then inserts a new record into the `biox_xref` table with the `xrefId`, `xrefSrc` (derived from `xref_db`), and `featureId`. The script ensures data integrity by validating the presence of gene names and rolling back any changes if an error occurs.

## Migration Checklist

- [ ] load-stat.py
- [ ] load_cancer.py
- [ ] load_sample_fake.py
- [ ] load_sample_tcga.py
- [ ] load_subject.py
- [ ] load_subject_fake.py
- [ ] load_subject_tcga.py
- [ ] new_load_boxplot.py
- [ ] new_load_dataset_fields.py
- [ ] new_load_dataset_records.py
- [ ] new_load_datasets.py
- [ ] new_load_de.py
- [ ] new_load_doid.py
- [x] new_load_feature.py
- [ ] new_load_sample.py
- [ ] new_load_tissue.py
- [x] new_load_xref.py
