# %%
# #!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Purpose
        Read in analysis table of GOV.UK appointments and match to ministers
        database
    Inputs
        - SQL: from analysis.[ukgovt.minister_govuk_people_page_content_20240503]
        - SQL: core.person
        - SQL: core.appointment
        - SQL: core.appointment_characteristics
        - SQL: core.post
        - SQL: core.organisation
    Outputs
        - TODO
    Parameters
        None
    Notes
        None
    Future enhancements
        - Read person_id as UNIQUEIDENTIFIER in both datasets and get rid
        of the conversion of df_govuk_appt['person_id'] to lowercase
'''

import os
import uuid

import pandas as pd
from rapidfuzz import fuzz
from sqlalchemy.dialects.mssql import BIT, DATE, FLOAT, NVARCHAR, UNIQUEIDENTIFIER

from ds_utils import database_operations as dbo

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
df_ifg_appt = pd.read_sql_query(
    '''
    select
        a.id appointment_id,
        p.id person_id,
        p.name person_name,
        case
            when p.is_mp = 1 then 'MP'
            when p.is_peer = 1 then 'Peer'
        end [MP/peer],
        t.name post_name,
        t.rank_equivalence post_rank,
        o.name organisation_name,
        o.short_name organisation_short_name,
        ac.cabinet_status,
        ac.is_on_leave,
        ac.is_acting,
        ac.leave_reason,
        ac.start_date,
        case
            when ac.end_date = '9999-12-31' then null
            else ac.end_date
        end end_date
    from core.person p
        inner join core.appointment a on
            p.id = a.person_id and
            isnull(p.start_date, '1900-01-01') <= a.start_date and
            p.end_date > a.start_date
        inner join core.appointment_characteristics ac on
            a.id = ac.appointment_id
        inner join core.post t on
            a.post_id = t.id
        inner join core.organisation o on
            t.organisation_id = o.id
    where
        ac.start_date >= '2010-05-11'
    ''',
    con=connection,
)

df_govuk_appt = pd.read_sql_query(
    """
    select
        g.appointment_id_govuk appointment_id,
        g.person_id,
        g.person_name,
        g.post_name_clean post_name,
        g.post_rank,
        g.is_on_leave,
        g.is_acting,
        g.leave_reason,
        g.organisation_name_clean organisation_name,
        g.organisation_short_name_clean organisation_short_name,
        g.appointment_start_date start_date,
        g.appointment_end_date end_date
    from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] g
    """,
    con=connection,
)

# %%
# EDIT DATA
# Convert date columns to datetime
df_govuk_appt['start_date'] = pd.to_datetime(df_govuk_appt['start_date'], errors='coerce')
df_govuk_appt['end_date'] = pd.to_datetime(df_govuk_appt['end_date'], errors='coerce')
df_ifg_appt['start_date'] = pd.to_datetime(df_ifg_appt['start_date'], errors='coerce')
df_ifg_appt['end_date'] = pd.to_datetime(df_ifg_appt['end_date'], errors='coerce')

# %%
# Set end dates of ongoing appointments to today's date
df_govuk_appt.loc[
    df_govuk_appt['end_date'].isnull(),
    'end_date'
] = pd.Timestamp.now().normalize()

df_ifg_appt.loc[
    df_ifg_appt['end_date'].isnull(),
    'end_date'
] = pd.Timestamp.now().normalize()

# %%
# JOIN DATASETS
# Initial match - exact match on person_id
df_merge = pd.merge(
    df_ifg_appt,
    df_govuk_appt,
    how='inner',
    on='person_id',
    suffixes=('_ifg', '_govuk')
)

# %%
# Exact match on organisation_short_name: 1 if match, 0.5 if not
df_merge['organisation_short_name_match'] = 0.5
df_merge.loc[
    df_merge['organisation_short_name_ifg'] == df_merge['organisation_short_name_govuk'],
    'organisation_short_name_match'
] = 1

# %%
# Fuzzy match on post_name
df_merge['post_name_match'] = 0
df_merge['post_name_match'] = df_merge.apply(
    lambda x: fuzz.ratio(x['post_name_ifg'], x['post_name_govuk']) / 100,
    axis=1
)

# %%
# Date match on start_date, end_date: 1 if exact match, minus 0.01 for each day difference,
# 0 if more than 100 days difference
df_merge['start_date_match'] = 1 - (
    abs(df_merge['start_date_ifg'] - df_merge['start_date_govuk']).dt.days / 100
)
df_merge['start_date_match'] = df_merge['start_date_match'].clip(lower=0)
df_merge['end_date_match'] = 1 - (
    abs(df_merge['end_date_ifg'] - df_merge['end_date_govuk']).dt.days / 100
)
df_merge['end_date_match'] = df_merge['end_date_match'].clip(lower=0)

df_merge['date_match'] = df_merge['start_date_match'] * 0.5 + df_merge['end_date_match'] * 0.5

# %%
# Calculate weighted average of matches
df_merge['match_score'] = (
    df_merge['organisation_short_name_match'] * 0.3 +
    df_merge['post_name_match'] * 0.5 +
    df_merge['date_match'] * 0.2
)

# %%
# Sort by appointment_id_ifg and match_score
df_merge = df_merge.sort_values(
    by=['person_name_ifg', 'appointment_id_ifg', 'match_score'],
    ascending=[True, True, False]
).reset_index(drop=True)

# %%
# Add columns for tracking matching
df_merge['reviewed'] = False
df_merge['match_accepted'] = False
df_merge['replace_post_name'] = False
df_merge['notes'] = None

# %%
# Auto-accept matches with match_score >= 1
df_merge.loc[
    df_merge['match_score'] >= 1,
    'match_accepted'
] = True
df_merge.loc[
    df_merge['appointment_id_ifg'].isin(
        df_merge.loc[
            df_merge['match_accepted'],
            'appointment_id_ifg'
        ]
    ),
    'reviewed'
] = True

# %%
# Auto-accept matches with organisation_short_name_match = 1, post_name_match = 1 and
# date_match >= 0.8
df_merge.loc[
    (df_merge['organisation_short_name_match'] == 1) &
    (df_merge['post_name_match'] == 1) &
    (df_merge['date_match'] >= 0.8),
    'match_accepted'
] = True

# %%
# Set reviewed to True for appointments that have been auto-accepted
df_merge.loc[
    df_merge['appointment_id_ifg'].isin(
        df_merge.loc[
            df_merge['match_accepted'],
            'appointment_id_ifg'
        ]
    ),
    'reviewed'
] = True

# %%
# SAVE TO DB
uuid_table_name = str(uuid.uuid4())

df_merge.to_sql(
    uuid_table_name,
    schema='workflow',
    con=connection,
    dtype={
        'appointment_id_ifg': UNIQUEIDENTIFIER,
        'person_id': UNIQUEIDENTIFIER,
        'person_name_ifg': NVARCHAR(256),
        'MP/peer': NVARCHAR(10),
        'post_name_ifg': NVARCHAR(256),
        'post_rank_ifg': NVARCHAR(256),
        'organisation_name_ifg': NVARCHAR(256),
        'organisation_short_name_ifg': NVARCHAR(256),
        'cabinet_status': NVARCHAR(256),
        'is_on_leave_ifg': BIT,
        'is_acting_ifg': BIT,
        'leave_reason_ifg': NVARCHAR(256),
        'start_date_ifg': DATE,
        'end_date_ifg': DATE,
        'appointment_id_govuk': UNIQUEIDENTIFIER,
        'person_name_govuk': NVARCHAR(256),
        'post_name_govuk': NVARCHAR(256),
        'post_rank_govuk': NVARCHAR(256),
        'organisation_name_govuk': NVARCHAR(256),
        'organisation_short_name_govuk': NVARCHAR(256),
        'is_on_leave_govuk': BIT,
        'is_acting_govuk': BIT,
        'leave_reason_govuk': NVARCHAR(256),
        'start_date_govuk': DATE,
        'end_date_govuk': DATE,
        'post_name_clean': NVARCHAR(256),
        'organisation_name_clean': NVARCHAR(256),
        'organisation_short_name_clean': NVARCHAR(256),
        'appointment_start_date': DATE,
        'appointment_end_date': DATE,
        'organisation_short_name_match': FLOAT,
        'post_name_match': FLOAT,
        'start_date_match': FLOAT,
        'end_date_match': FLOAT,
        'date_match': FLOAT,
        'match_score': FLOAT,
        'reviewed': BIT,
        'match_accepted': BIT,
        'replace_post_name': BIT,
        'notes': NVARCHAR(512),
    },
    index=False,
    if_exists='replace',
)

# %%
