# %%
# #!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Purpose
        Clean GOV.UK person page data
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
import utils.utils as utils

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
# CLEAN DATA
# Remove ampersands
df['post_name_clean'] = df['post_name_clean'].apply(utils.replace_ampersand)

# %%
# Identify ministers on leave and doing roles in an acting capacity
df[['post_name_clean', 'is_on_leave', 'is_acting', 'leave_reason']] = pd.DataFrame(
    df['post_name_clean'].apply(utils.identify_ministers_on_leave_acting).to_list()
)

# %%
# Remove joint post names
df['post_name_clean'] = df['post_name_clean'].apply(utils.remove_joint_post_name)

# %%
# Handle post names that are denormalised by having an equalities minister name appended
df['post_name_clean'] = df['post_name_clean'].apply(utils.handle_equalities_minister_post_name)

# %%
# Handle Parliamentary Secretary post names
df[['post_name_clean', 'post_rank']] = pd.DataFrame(
    df['post_name_clean'].apply(utils.handle_parliamentary_secretary_post_name).to_list()
)

# %%
# Remove details of Lords minister roles
df['post_name_clean'] = df['post_name_clean'].apply(utils.remove_lords_minister_post_names)

# %%
# Standardise MoS, PUSS post name
# Ref: https://stackoverflow.com/a/66267940/4659442
df[['post_name_clean', 'post_rank']] = pd.DataFrame(
    df['post_name_clean'].apply(utils.standardise_mos_puss_post_name).to_list()
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
