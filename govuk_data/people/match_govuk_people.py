# %%
# #!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Purpose
        Read in post-2010 ministers and gov.uk people strings, fuzzy match
        and manual match and save to SQL
    Inputs
        - SQL: core.person
        - SQL: core.appointment
        - SQL: reference.[ukgovt.minister_ids_govuk_strings]
        - Excel: data/match_20240503.xlsx
    Outputs
        - Excel: data/match_20240503.xlsx
        - SQL: analysis.[ukgovt.minister_ids_govuk_strings_20240503]
    Parameters
        None
    Notes
        None
'''

import os

import pandas as pd
import pandas.io.formats.excel
import sqlalchemy
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

from ds_utils import database_operations as dbo
from ds_utils import string_operations as so
from utils.fuzzy_match import fuzzy_merge

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
# READ IN DATA FOR MATCHING
df_ifg_minister = pd.read_sql_query(
    '''
    select *
    from core.person p
    where
        exists (
            select *
            from core.appointment a
            where
                p.id = a.person_id and
                a.end_date > '2010-05-06'
        ) and
        not exists (
            select *
            from reference.[ukgovt.minister_ids_govuk_strings] g
            where
                p.id = g.id
        )
    ''',
    con=connection,
    index_col='id'
)

# List of gov.uk identifiers
df_govuk_person = pd.read_sql_table(
    'ukgovt.govuk_strings_people_20240503',
    schema='source',
    con=connection
)

# %%
# CLEAN DATA
df_govuk_person['name'] = df_govuk_person['name'].apply(
    lambda x: so.strip_name_title(x, exclude_peerage=True)
)

# Strip 'The Rt Hon', 'MP' from names
df_govuk_person['name'] = df_govuk_person['name'].replace(
    {
        '(The )*Rt Hon': '',
        'MP': ''
    },
    regex=True
).str.strip()

# %%
# FUZZY MATCH
df_match = fuzzy_merge(
    df_ifg_minister,
    df_govuk_person,
    column_left='name',
    column_right='name',
    score_cutoff=0,
    limit=1,
    drop_cols=None
)

# %%
# EXPORT THE TABLE OF MATCHES, FOR MANUAL QA
pandas.io.formats.excel.ExcelFormatter.header_style = None

df_match[[
    'match_score',
    'name_df_left',
    'name_df_right',
    'govuk_string',
]].to_excel(
    'data/match_20240503.xlsx'
)

# %%
# INGEST REVIEWED MATCHES
df_reviewed = pd.read_excel(
    'data/match_20240503.xlsx',
    index_col=None
)

# %%
# EDIT REVIEWED MATCHES
# This picks accepted fuzzy matches and supplied manual matches
df_reviewed = pd.concat(
    [
        df_reviewed[
            df_reviewed['Accept'] == 'Y'
        ][[
            'df_left_id',
            'df_right_id',
            'name_df_left',
            'name_df_right',
            'govuk_string'
        ]],
        df_reviewed[
            (df_reviewed['Accept'] == 'N') &
            (df_reviewed['Replacement name'].notna())
        ][[
            'df_left_id',
            'df_right_id',
            'name_df_left',
            'Replacement name',
            'Replacement govuk_string'
        ]].rename(
            columns={
                'Replacement name': 'name_df_right',
                'Replacement govuk_string': 'govuk_string'
            }
        )
    ]
)

# %%
# SAVE TO
df_reviewed[[
    'df_left_id',
    'name_df_left',
    'govuk_string',
]].rename(
    columns={
        'df_left_id': 'id',
        'name_df_left': 'name'
    }
).to_sql(
    'ukgovt.minister_ids_govuk_strings_20240503',
    schema='analysis',
    con=connection,
    dtype={
        'id': UNIQUEIDENTIFIER,
        'name': sqlalchemy.types.NVARCHAR(length=255),
        'govuk_string': sqlalchemy.types.NVARCHAR(length=255)
    },
    index=False,
)

# %%
