# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
import dataiku
from dataiku import pandasutils as pdu
import pandas as pd
import scipy.stats as scipy
from AB_testing.config import *
from AB_testing.stats_tests import *

# Read the dataset as a Pandas dataframe in memory
# Note: here, we only read the first 100K rows. Other sampling options are available
dataset_export_file = dataiku.Dataset("export_file")
df = dataset_export_file.get_dataframe(limit=100000)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
config = config()
stats_tests = stats_tests(config)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
df_out = stats_tests.run_uplift_calculator(df)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
ab_all_results = dataiku.Dataset("AB_all_results")
ab_all_results.write_with_schema(df_out)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
df_final = df_out[['product','volume_count_A','volume_count_B','sales_cnt_A','sales_cnt_B',
                   'SRR_A','errSRR_A','SRR_B','errSRR_B','S_r_uplift','S_p-score']]
df_final = df_final.round({'SRR_A':3,'errSRR_A':4,'SRR_B':3,'errSRR_B':4,'S_p-score':0,'S_r_uplift':3})

ab_summary = dataiku.Dataset("AB_summary")
ab_summary.write_with_schema(df_final)

