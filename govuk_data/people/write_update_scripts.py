# %%
# #!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Purpose
        Write scripts to update ministers database records based on
        results of matching
    Inputs
        - SQL: workflow.<uuid>
        - script: 'utils/identify_posts_to_add.sql'
        - script: 'utils/identify_appointments_to_edit.sql'
        - script: 'utils/create_post_count.sql'
        - script: 'utils/create_post.sql'
        - script: 'utils/update_appointment.sql'
        - script: 'utils/update_appointment_count.sql'
    Outputs
        None
    Parameters
        None
    Notes
        None
'''

import os

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
# READ IN SQL SCRIPTS
# Identify posts to add
with open('utils/identify_posts_to_add.sql', 'r') as file:
    identify_posts_to_add = file.read()

# Identify appointments to edit
with open('utils/identify_appointments_to_edit.sql', 'r') as file:
    identify_appointments_to_edit = file.read()

# Create post count
with open('utils/create_post_count.sql', 'r') as file:
    create_post_count = file.read()

# Create post
with open('utils/create_post.sql', 'r') as file:
    create_post = file.read()

# Update appointment count
with open('utils/update_appointment_count.sql', 'r') as file:
    update_appointment_count = file.read()

# Update appointment
with open('utils/update_appointment.sql', 'r') as file:
    update_appointment = file.read()

# %%
# READ IN DATA TO USE IN SCRIPTS
df_posts_to_add = pd.read_sql_query(
    sql=identify_posts_to_add,
    con=connection,
)

df_appointments_to_edit = pd.read_sql_query(
    sql=identify_appointments_to_edit,
    con=connection,
)

# %%
# Escape single quotes in post names
df_posts_to_add['post_name'] = df_posts_to_add[
    'post_name'
].str.replace("'", "''")
df_appointments_to_edit['post_name_old'] = df_appointments_to_edit[
    'post_name_old'
].str.replace("'", "''")
df_appointments_to_edit['post_name_new'] = df_appointments_to_edit[
    'post_name_new'
].str.replace("'", "''")

# %%
# PRODUCE SCRIPTS
# Add posts
add_posts_code = '--- SET HOLD\nset noexec on\n\n'

for index, row in df_posts_to_add.iterrows():

    # Check if number of records affected is as expected
    add_posts_count_snippet = create_post_count.format(
        post_name=row['post_name'],
        post_rank=row['post_rank'],
        organisation_name=row['organisation_name'],
        organisation_short_name=row['organisation_short_name'],
        organisation_start_date=row['organisation_start_date'],
        organisation_end_date=row['organisation_end_date'],
    )
    add_posts_count_snippet = add_posts_count_snippet.replace(
        "= 'None'", "is null"
    )

    assert pd.read_sql_query(
        sql=add_posts_count_snippet,
        con=connection,
    ).iloc[0, 0] == 1, (
        f"Expected 1 record to be affected, but {add_posts_count_snippet} "
        f"affected {
            pd.read_sql_query(sql=add_posts_count_snippet, con=connection).iloc[0, 0]
        } records"
    )

    # Produce code
    add_posts_snippet = create_post.format(
        post_name=row['post_name'],
        post_rank=row['post_rank'],
        organisation_name=row['organisation_name'],
        organisation_short_name=row['organisation_short_name'],
        organisation_start_date=row['organisation_start_date'],
        organisation_end_date=row['organisation_end_date'],
    )
    add_posts_snippet = add_posts_snippet.replace(
        "= 'None'", "is null"
    )

    add_posts_code += add_posts_snippet + '\n'

print(add_posts_code)

# %%
# Update appointments
update_appointments_code = '--- SET HOLD\nset noexec on\n\n'

for index, row in df_appointments_to_edit.iterrows():

    # Check if number of records affected is as expected
    update_appointments_count_snippet = update_appointment_count.format(
        person_name=row['person_name'],
        post_name_old=row['post_name_old'],
        post_name_new=row['post_name_new'],
        organisation_name=row['organisation_name'],
        organisation_short_name=row['organisation_short_name'],
        post_rank_old=row['post_rank_old'],
        post_rank_new=row['post_rank_new'],
        start_date=row['start_date'],
        end_date=row['end_date'],
    )

    assert pd.read_sql_query(
        sql=update_appointments_count_snippet,
        con=connection,
    ).iloc[0, 0] == 1, (
        f"Expected 1 record to be affected, but {update_appointments_count_snippet} "
        f"affected {
            pd.read_sql_query(sql=update_appointments_count_snippet, con=connection).iloc[0, 0]
        } records"
    )

    # Produce code
    update_appointments_snippet = update_appointment.format(
        person_name=row['person_name'],
        post_name_old=row['post_name_old'],
        post_name_new=row['post_name_new'],
        organisation_name=row['organisation_name'],
        organisation_short_name=row['organisation_short_name'],
        post_rank_old=row['post_rank_old'],
        post_rank_new=row['post_rank_new'],
        start_date=row['start_date'],
        end_date=row['end_date'],
    )

    update_appointments_code += update_appointments_snippet + '\n'

print(update_appointments_code)

# %%
