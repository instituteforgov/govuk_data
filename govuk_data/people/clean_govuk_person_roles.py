# %%
# #!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Purpose
        Read in gov.uk person page data from API endpoint
    Inputs
        - SQL: analysis.ukgovt.minister_govuk_people_page_content_20240503
    Outputs
        - SQL: analysis.ukgovt.minister_govuk_people_page_content_20240503
    Parameters
        None
    Notes
        None
'''

import os

import pandas as pd
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

from ds_utils import database_operations as dbo
from utils.utils import standardise_mos_puss_post_name

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
# READ IN ANALYSIS TABLE
df = pd.read_sql_query(
    '''
    select *
    from [analysis].[ukgovt.minister_govuk_people_page_content_20240503]
    ''',
    con=connection
)

# %%
# CLEAN POST NAME AND ADD POST RANK
# Ref: https://stackoverflow.com/a/66267940/4659442
df.insert(
    df.columns.get_loc('post_name') + 1,
    'post_name_clean',
    None
)
df.insert(
    df.columns.get_loc('post_name') + 2,
    'post_rank',
    None
)

df[['post_name_clean', 'post_rank']] = pd.DataFrame(
    df['post_name'].apply(standardise_mos_puss_post_name).to_list()
)

# %%
df.to_sql(
    'ukgovt.minister_govuk_people_page_content_20240503',
    schema='analysis',
    con=connection,
    dtype={
        'person_id': UNIQUEIDENTIFIER,
        'person_id_govuk': UNIQUEIDENTIFIER,
        'appointment_id_govuk': UNIQUEIDENTIFIER,
        'post_id_govuk': UNIQUEIDENTIFIER,
        'organisation_id_govuk': UNIQUEIDENTIFIER,
    },
    index=False,
    if_exists='replace',
)

# %%
