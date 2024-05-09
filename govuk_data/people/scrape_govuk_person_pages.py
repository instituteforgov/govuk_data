# %%
# #!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Purpose
        Read in gov.uk person page data from API endpoint
    Inputs
        - SQL: reference.[ukgovt.minister_ids_govuk_strings]
        - API: https://www.gov.uk/api/content/government/people/<person_string>
    Outputs
        - pkl: data/df_person_page.pkl_20240503
        - SQL: analysis.ukgovt.minister_govuk_people_page_content_20240503
    Parameters
        - base_url: Base URL for API request
        - headers: Headers for API request
        - connection_retries: Number of connection retries
        - backoff_factor: Backoff factor for connection retries
    Notes
        None
    Future enhancements
        - Add handling for rate limiting https://content-api.publishing.service.gov.uk/#rate-limiting       # noqa: E501
            - NB: Hasn't been a problem so far, scraping ~400 pages without adding a delay between
            requests
        - Save page json to Azure Blob Storage
'''

import os

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from urllib3.util.retry import Retry

from ds_utils import database_operations as dbo
from ds_utils import dataframe_operations as dfo

# %%
# SET PARAMETERS
base_url = 'https://www.gov.uk/api/content/government/people/'
headers = {'Accept': 'application/json'}
connection_retries = 5
backoff_factor = 0.5

# %%
# CONNECT TO D/B
connection = dbo.connect_sql_db(
    driver='pyodbc',
    driver_version=os.environ['odbc_driver'],
    dialect='mssql',
    server=os.environ['odbc_server'],
    database=os.environ['odbc_database'],
    authentication=os.environ['odbc_authentication'],
    username=os.environ['odbc_username'],
)

# %%
# READ IN LIST OF GOV.UK PEOPLE STRINGS
df_ifg_minister = pd.read_sql_query(
    '''
    select *
    from reference.[ukgovt.govuk_strings_people]
    ''',
    con=connection,
    index_col='id'
)

# %%
# RETRIEVE DATA FROM API
row_list = []

session = requests.Session()
retry = Retry(connect=connection_retries, backoff_factor=backoff_factor)
adapter = HTTPAdapter(max_retries=retry)
session.mount('https://', adapter)

for index, row in df_ifg_minister.iterrows():
    r = session.get(
        base_url + row['govuk_string'],
        headers=headers
    )

    # Add ifg_id to json
    row = {}
    row['ifg_person_id'] = index
    row.update(r.json())

    # Add to list
    row_list.append(row)

# %%
# FLATTEN JSON
df_person_page = pd.json_normalize(row_list)

# %%
# CARRY OUT CHECKS ON DATA
# Check number of rows is as expected
assert df_person_page.shape[0] == df_ifg_minister.shape[0], \
    'Number of rows in df_person_page does not match df_ifg_minister'

# %%
# SAVE TO PICKLE
df_person_page.to_pickle('data/df_person_page.pkl_20240503')

# %%
# EDIT DATA
# Further flatten json
df_temp = dfo.flatten_nested_json_columns(
    df_person_page
)

# %%
# SAVE TO SQL
df_temp.to_sql(
    'ukgovt.minister_govuk_people_page_content_20240503',
    schema='analysis',
    con=connection,
    dtype={
        'ifg_person_id': UNIQUEIDENTIFIER,
    },
    index=False,
    if_exists='replace',
)
