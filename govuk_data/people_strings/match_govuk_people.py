# %%
'''
    Purpose
        Read in post-2010 ministers and GOV.UK people strings, fuzzy match
        and manual match and save to SQL
    Inputs
        - SQL: core.person
        - SQL: core.appointment
        - SQL: reference.[ukgovt.govuk_strings_people]
        - SQL: source.[ukgovt.govuk_strings_people_<datestamp>]
        - Excel: govuk_data/people_strings/data/match_<datestamp>.xlsx
    Outputs
        - Excel: govuk_data/people_strings/data/match_<datestamp>.xlsx
        - SQL: analysis.[ukgovt.minister_ids_govuk_strings_<datestamp>]
    Parameters
        None
    Notes
        - Needs to be run in two stages:
            - 1. Up to the stage where fuzzy match results are exported using to_excel()
            - 2. From ingesting the results of manual review of the matches onwards
'''

import os
import re

from ds_utils import matching_operations as mo
from ds_utils import database_operations as dbo
from ds_utils import string_operations as so
import pandas as pd
import pandas.io.formats.excel
import sqlalchemy
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

# %%
# SET CONSTANTS
DATESTAMP = '20260428'
PREFIXES = ['The Rt Hon', 'Rt Hon', 'Sir']
SUFFIXES = ['GBE', 'KBE', 'DBE', 'CBE', 'OBE', 'MBE', 'TD', 'KC', 'QC', 'MP']

# %%
# CONNECT TO D/B
connection = dbo.connect_sql_db(
    driver='pyodbc',
    driver_version=os.environ['ODBC_DRIVER'],
    dialect='mssql',
    server=os.environ['ODBC_SERVER'],
    database=os.environ['ODBC_DATABASE'],
    authentication=os.environ['ODBC_AUTHENTICATION'],
    username=os.environ["AZURE_CLIENT_ID"],
    password=os.environ["AZURE_CLIENT_SECRET"],
)

# %%
# READ IN DATA FOR MATCHING
# NB: This includes a row for every record in core.person - so where someone's person record is split across two records (e.g. because they've changed name), the table we use as the basis for matching will include both records
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
                a.end_date > '2010-05-11'
        ) and
        not exists (
            select *
            from reference.[ukgovt.govuk_strings_people] g
            where
                p.id = g.id
        )
    ''',
    con=connection,
    index_col='id'
)

# List of GOV.UK identifiers
df_govuk_person = pd.read_sql_table(
    f'ukgovt.govuk_strings_people_{DATESTAMP}',
    schema='source',
    con=connection
)

# %%
# EDIT DATA
# Set index
df_govuk_person.set_index('id', inplace=True)

# Strip titles from names
df_govuk_person['name'] = df_govuk_person['name'].apply(
    lambda x: so.strip_name_title(x, exclude_peerage=True)
)

# Strip prefixes and suffixes from names
prefix_re = re.compile(
    r'^(?:' + '|'.join(re.escape(p) for p in PREFIXES) + r')\s+'
)
suffix_re = re.compile(
    r'\s+(?:' + '|'.join(re.escape(s) for s in SUFFIXES) + r')$'
)


def strip_honorifics(name: str) -> str:
    """Remove known prefixes and suffixes, repeating until none remain."""
    if not isinstance(name, str):
        return name
    prev = None
    while prev != name:
        prev = name
        name = prefix_re.sub('', name)
        name = suffix_re.sub('', name)
    return name.strip()


df_govuk_person['name'] = df_govuk_person['name'].apply(strip_honorifics)

# %%
# FUZZY MATCH
df_match = mo.fuzzy_merge(
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
    f'govuk_data/people_strings/data/match_{DATESTAMP}.xlsx'
)

# %%
# INGEST REVIEWED MATCHES
df_reviewed = pd.read_excel(
    f'govuk_data/people_strings/data/match_{DATESTAMP}.xlsx',
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
    f'ukgovt.minister_ids_govuk_strings_{DATESTAMP}',
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
