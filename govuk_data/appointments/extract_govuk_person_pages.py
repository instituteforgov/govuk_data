# %%
'''
    Purpose
        Extract GOV.UK person page data from the GOV.UK Content API and save to
        SQL
    Inputs
        - SQL: reference.[ukgovt.govuk_strings_people]
        - API: https://www.gov.uk/api/content/government/people/<person_string>
    Outputs
        - pkl: data/df_person_page.pkl_<datestamp>
        - SQL: source.[ukgovt.minister_govuk_people_page_content_<datestamp>]
    Parameters
        - base_url: Base URL for API request
        - headers: Headers for API request
        - connection_retries: Number of connection retries
        - backoff_factor: Backoff factor for connection retries
    Notes
        None
    Future enhancements
        - Add handling for rate limiting https://content-api.publishing.service.gov.uk/#rate-limiting       # noqa: E501
            - NB: Hasn't been a problem so far, extracting ~400 pages without adding a delay between
            requests
        - Save page json to Azure Blob Storage
'''

import os
from uuid import uuid4

from ds_utils import database_operations as dbo
from ds_utils import dataframe_operations as dfo
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER
from urllib3.util.retry import Retry

# %%
# SET CONSTANTS
DATESTAMP = '20240503'
base_url = 'https://www.gov.uk/api/content/government/people/'
headers = {'Accept': 'application/json'}
connection_retries = 5
backoff_factor = 0.5

# %%
# CONNECT TO D/B
connection = dbo.connect_sql_db(
    driver='pyodbc',
    driver_version=os.environ['ODBC_DRIVER'],
    dialect='mssql',
    server=os.environ['ODBC_SERVER'],
    database=os.environ['ODBC_DATABASE'],
    authentication=os.environ['ODBC_AUTHENTICATION'],
    username=os.environ['ODBC_USERNAME'],
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
# Create df
df_person_page = pd.DataFrame(row_list)

# %%
# CARRY OUT CHECKS ON DATA
# Check number of rows is as expected
assert df_person_page.shape[0] == df_ifg_minister.shape[0], \
    'Number of rows in df_person_page does not match df_ifg_minister'

# %%
# SAVE TO PICKLE
df_person_page.to_pickle(f'data/df_person_page.pkl_{DATESTAMP}')

# %%
# EDIT DATA
# Further flatten json
df_person_page_flat = dfo.flatten_nested_json_columns(
    df_person_page
)

# %%
# Add unique row ID
df_person_page_flat.insert(0, 'row_id', None)

df_person_page_flat['row_id'] = df_person_page_flat['ifg_person_id'].apply(
    lambda x: uuid4()
)

# %%
# Strip whitespace from all string columns
df_person_page_flat = df_person_page_flat.map(
    lambda x: x.strip() if isinstance(x, str) else x
)

# %%
# SAVE TO SQL
df_person_page_flat.to_sql(
    f'ukgovt.minister_govuk_people_page_content_{DATESTAMP}',
    schema='source',
    con=connection,
    dtype={
        'ifg_person_id': UNIQUEIDENTIFIER,
    },
    index=False,
    if_exists='replace',
)
