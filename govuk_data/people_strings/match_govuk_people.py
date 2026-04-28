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
            - The output table of fuzzy matches, with manual review columns filled in as follows:
                - 'Accept': 'Y' for accepted matches, 'N' for rejected matches
                - 'Replacement name': The actual name of the individual, rather than the suggested match, where we wish to supply an alternative
                    - NB: This is likely to match name_df_left
                    - NB: Where a row is the second (or subsequent) record for a given individual, this should be left blank
                - 'Replacement govuk_string': The actual GOV.UK string for the individual, rather than the suggested match, where we wish to supply an alternative
                    - NB: Where a row is the second (or subsequent) record for a given individual, this should be left blank
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

# Strip honorific prefixes and post-nominal suffixes from names
df_govuk_person['name'] = df_govuk_person['name'].apply(
    lambda x: so.strip_name_affixes(x, exclude_peerage=True)
)

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

# Rank matches by score for each left record
df_match['duplicate_flag_df_left'] = (
    df_match.groupby(level='df_left_id')['match_score']
    .rank(method='first', ascending=False)
    .astype(int)
)

# Order by df_left_id and duplicate_flag_df_left
df_match.sort_values(['df_left_id', 'duplicate_flag_df_left'], inplace=True)

# %%
# EXPORT THE TABLE OF MATCHES, FOR MANUAL QA
pandas.io.formats.excel.ExcelFormatter.header_style = None

df_match["Accept"] = None
df_match["Replacement name"] = None
df_match["Replacement govuk_string"] = None

df_match[[
    'duplicate_flag_df_left',
    'match_score',
    'name_df_left',
    'name_df_right',
    'govuk_string',
    'Accept',
    'Replacement name',
    'Replacement govuk_string',
]].to_excel(
    f'govuk_data/people_strings/data/match_{DATESTAMP}.xlsx',
    merge_cells=False
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
