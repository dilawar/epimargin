#!python3 
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
import requests

from adaptive.utils import assume_missing_0

"""code to extracts logarithmic growth rates for india-specific data"""

# states created after the 2001 census
new_states = set("Telangana")

# states renamed in 2011 
renames = { 
    "Orissa"      : "Odisha",
    "Pondicherry" : "Puducherry"
}

columns_v1 = v1 = [
    "patient number",
    "state patient number",
    "date announced",
    "age bracket",
    "gender",
    "detected city",
    "detected district",
    "detected state",
    "current status",
    "notes",
    "contracted from which patient (suspected)",
    "nationality",
    "type of transmission",
    "status change date",
    "source_1",
    "source_2",
    "source_3",
    "backup note"
]

columns_v2 = v2 = [
    'patient number',
    'state patient number',
    'date announced',
    'estimated onset date',
    'age bracket',
    'gender',
    'detected city',
    'detected district',
    'detected state',
    'state code',
    'current status',
    'notes',
    'contracted from which patient (suspected)',
    'nationality',
    'type of transmission',
    'status change date',
    'source_1',
    'source_2',
    'source_3',
    'backup notes'
]

drop_cols = {
    "age bracket",
    "gender",
    "detected city",
    # "detected district",
    "notes",
    "contracted from which patient (suspected)",
    "nationality",
    "source_1",
    "source_2",
    "source_3",
    "backup note",
    "backup notes",
    "type of transmission"
}

columns_v3 = v3 = [
    'Patient Number',
    'State Patient Number',
    'Date Announced',
    'Estimated Onset Date',
    'Age Bracket',
    'Gender',
    'Detected City',
    'Detected District',
    'Detected State',
    'State code',
    'Current Status',
    'Notes',
    'Contracted from which Patient (Suspected)',
    'Nationality',
    'Type of transmission',
    'Status Change Date',
    'Source_1',
    'Source_2',
    'Source_3',
    'Backup Notes',
    'Num cases'
]

drop_cols_v3 = {
    "Age Bracket",
    "Gender",
    "Detected City",
    "Notes",
    'Contracted from which Patient (Suspected)', 
    'Nationality',
    "Source_1",
    "Source_2",
    "Source_3",
    "Backup Notes",
    "State Patient Number",
    "State code",
    "Estimated Onset Date",
    "Type of transmission"
}

columns_v4 = v4 = [
    'Entry_ID', 
    'State Patient Number', 
    'Date Announced', 
    'Age Bracket',
    'Gender', 
    'Detected City', 
    'Detected District', 
    'Detected State',
    'State code', 
    'Num Cases', 
    'Current Status',
    'Contracted from which Patient (Suspected)', 
    'Notes', 
    'Source_1',
    'Source_2', 
    'Source_3', 
    'Nationality', 
    'Type of transmission',
    'Status Change Date', 
    'Patient Number'
]

drop_cols_v4 = {
    "Entry_ID",
    'Age Bracket',
    'Gender', 
    'Detected City',
    'State code',
    'Contracted from which Patient (Suspected)',
    'Notes', 
    'Source_1',
    'Source_2', 
    'Source_3', 
    'Nationality', 
    'Type of transmission',
    "State Patient Number"
}

column_ordering_v4  = [
    'Patient Number',
    'Date Announced',
    'Detected District',
    'Detected State',
    'Current Status',
    'Status Change Date',
    'Num cases'
]

current_endpoint_num = 4

def download_data(data_path: Path, today, base_url='https://api.covid19india.org/csv/latest/'):

    for i in range(current_endpoint_num):
        api_file = 'raw_data' + str(i + 1) + '.csv'
        filename = today + '_' + api_file
        if not (data_path/filename).exists():
            url = base_url + api_file
            response = requests.get(url)
            (data_path/filename).write_bytes(response.content)

# load data until April 26
def load_data_v3(path: Path):
    cases = pd.read_csv(path, 
        usecols     = set(columns_v3) - drop_cols_v3,
        dayfirst    = True, # source data does not have consistent date format so cannot rely on inference
        parse_dates = ["Date Announced", "Status Change Date"])
    return cases

# load data for April 27 - May 09  
def load_data_v4(path: Path):
    cases = pd.read_csv(path, 
        usecols     = set(columns_v4) - drop_cols_v4,
        dayfirst    = True, # source data does not have consistent date format so cannot rely on inference
        parse_dates = ["Date Announced", "Status Change Date"])
    cases["Num cases"] = cases["Num Cases"]
    return cases[column_ordering_v4]

# calculate daily totals and growth rate
def get_time_series(df: pd.DataFrame) -> pd.DataFrame:
    totals = df.groupby(["Status Change Date", "Current Status"])["Num cases"].agg(lambda counts: np.sum(np.abs(counts)))
    if len(totals) == 0:
        return pd.DataFrame()
    totals = totals.unstack().fillna(0)
    totals["date"]     = totals.index
    totals["time"]     = (totals["date"] - totals["date"].min()).dt.days
    totals["logdelta"] = np.log(assume_missing_0(totals, "Hospitalized") - assume_missing_0(totals, "Recovered") - assume_missing_0(totals, "Deceased"))
    return totals

def load_all_data(v3_paths: Sequence[Path], v4_paths: Sequence[Path]) -> pd.DataFrame:
    cases_v3 = [load_data_v3(path) for path in v3_paths]
    cases_v4 = [load_data_v4(path) for path in v4_paths]
    all_cases = pd.concat(cases_v3 + cases_v4)
    all_cases["Status Change Date"] = all_cases["Status Change Date"].fillna(all_cases["Date Announced"])
    return all_cases.dropna(subset = ["Detected State"])

# assuming analysis for data structure from COVID19-India saved as resaved, properly-quoted file (v1 and v2)
def load_data(datapath: Path, reduced: bool = False, schema: Optional[Sequence[str]] = None) -> pd.DataFrame: 
    if not schema:
        schema = columns_v1
    return pd.read_csv(datapath, 
        skiprows    = 1, # supply fixed header in order to deal with Google Sheets export issues 
        names       = schema, 
        usecols     = (lambda _: _ not in drop_cols) if reduced else None,
        dayfirst    = True, # source data does not have consistent date format so cannot rely on inference
        parse_dates = ["date announced", "status change date"])

def load_population_data(pop_path: Path) -> pd.DataFrame:
    return pd.read_csv(pop_path, names = ["name", "pop"])\
             .sort_values("name")

def load_migration_matrix(matrix_path: Path, populations: np.array) -> np.matrix:
    M  = np.loadtxt(matrix_path, delimiter=',') # read in raw data
    M *= populations[:,  None]                  # weight by population
    M /= M.sum(axis = 0)                        # normalize
    return M 

def district_migration_matrices(
    matrix_path: Path, 
    states: Sequence[str]) -> Dict[str, np.matrix]:
    mm = pd.read_csv(matrix_path)
    aggregations = dict()
    for col in  ['D_StateCensus2001', 'D_DistrictCensus2001', 'O_StateCensus2001', 'O_DistrictCensus2001']:
        mm[col] = mm[col].str.title().str.replace("&", "and")
    for state in  states:
        mm_state = mm[(mm.D_StateCensus2001 == state) & (mm.O_StateCensus2001 == state)]
        pivot    = mm_state.pivot(index = "D_DistrictCensus2001", columns = "O_DistrictCensus2001", values = "NSS_STMigrants").fillna(0)
        M  = np.matrix(pivot)
        Mn = M/M.sum(axis = 0)
        Mn[np.isnan(Mn)] = 0
        aggregations[state] = (
            pivot.index, 
            mm_state.groupby("O_DistrictCensus2001")["O_Population_2011"].agg(lambda x: list(x)[0]).values, 
            Mn
        )
    return aggregations 