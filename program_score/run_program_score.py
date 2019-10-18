# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# -*- coding: utf-8 -*-
import dataiku
import pandas as pd, numpy as np
from dataiku import pandasutils as pdu
from program_score.config import *
from program_score.program_score_prep import *

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# Read recipe inputs
base_programscore_v12_performance_scores = dataiku.Dataset("base_programscore_v12_performance_scores")
df = base_programscore_v12_performance_scores.get_dataframe()

config = config()
program_score_prep = program_score_prep(config)

df_prep = program_score_prep.calculate_program_score_from_weights(df)

# -------------------------------------------------------------------------------- NOTEBOOK-CELL: CODE
# Write recipe outputs
atc_programscore_data = dataiku.Dataset("ATC_programscore_data")
atc_programscore_data.write_with_schema(df_prep)