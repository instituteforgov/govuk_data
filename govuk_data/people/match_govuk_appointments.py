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
    ''',
    con=connection,
)

# List of gov.uk identifiers
df_govuk_appt = pd.read_sql_query(
    """
    select
        g.person_id,
        g.person_name,
        g.post_name_clean post_name,
        g.post_rank,
        g.is_on_leave,
        g.is_acting,
        g.leave_reason,
        g.organisation_name_clean organisation_name,
        g.organisation_short_name_clean organisation_short_name,
        g.appointment_start_date,
        g.appointment_end_date
    from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] g
    """,
    con=connection,
)

# %%
# CLEAN DATA
# Convert df_ifg_appt['person_id'] to UUID
df_ifg_appt['person_id'] = df_ifg_appt['person_id'].apply(
    lambda x: uuid.UUID(x)
)

# %%
# JOIN DATASETS
# Initial match - exact match on person_id
pd.merge(
    df_ifg_appt,
    df_govuk_appt,
    how='inner',
    on='person_id',
)
