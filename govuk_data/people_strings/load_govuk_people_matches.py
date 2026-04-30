# %%
'''
    Purpose
        Ingest manually reviewed GOV.UK people string matches and write to SQL
    Inputs
        - Excel: govuk_data/people_strings/data/match_<datestamp>.xlsx
            - The output table of fuzzy matches, with manual review columns filled in as follows:
                - 'Accept': 'Y' for accepted matches, 'N' for rejected matches
                - 'Replacement name': The actual name of the individual, rather than the suggested match, where we wish to supply an alternative
                    - NB: This is likely to match name_df_left
                    - NB: Where a row is the second (or subsequent) record for a given individual, this should be left blank
                - 'Replacement govuk_string': The actual GOV.UK string for the individual, rather than the suggested match, where we wish to supply an alternative
                    - NB: Where a row is the second (or subsequent) record for a given individual, this should be left blank
    Outputs
        - SQL: analysis.[ukgovt.minister_ids_govuk_strings_<datestamp>]
    Parameters
        None
    Notes
        - Run after match_govuk_people.py and manual review of the exported Excel file
'''

import os

from ds_utils import database_operations as dbo
import pandas as pd
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
# SAVE TO SQL
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
