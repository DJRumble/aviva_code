# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
import dataiku
from dataiku import pandasutils as pdu
import pandas as pd
import scipy.stats as scipy
from AB_testing.config import *
from AB_testing.stats_tests import *

# Read the dataset as a Pandas dataframe in memory
# Note: here, we only read the first 100K rows. Other sampling options are available
# Read recipe inputs
time_series_I = dataiku.Dataset("time_series_I")
time_series_I_df = time_series_I.get_dataframe()

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
config = config()
stats_tests = stats_tests(config)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
bayesian_summary_df = stats_tests.run_bayesian_test(time_series_I_df)

# Write recipe outputs
bayesian_summary = dataiku.Dataset("bayesian_summary")
bayesian_summary.write_with_schema(bayesian_summary_df)


