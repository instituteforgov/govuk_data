# %%
# #!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Purpose
        Write script to add new posts based on results of matching
    Inputs
        - SQL: workflow.<uuid>
        - script: 'utils/identify_posts_to_add.sql'
        - script: 'utils/create_post_count.sql'
        - script: 'utils/create_post.sql'
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

# Create post count
with open('utils/create_post_count.sql', 'r') as file:
    create_post_count = file.read()

# Create post
with open('utils/create_post.sql', 'r') as file:
    create_post = file.read()

# %%
# READ IN DATA TO USE IN SCRIPTS
df_posts_to_add = pd.read_sql_query(
    sql=identify_posts_to_add,
    con=connection,
)

# %%
# Escape single quotes in post names
df_posts_to_add['post_name'] = df_posts_to_add[
    'post_name'
].str.replace("'", "''")

# %%
# PRODUCE SCRIPT
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
