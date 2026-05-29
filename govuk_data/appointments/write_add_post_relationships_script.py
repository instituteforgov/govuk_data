# %%
"""
    Purpose
        Write script to add new posts to core.post_relationships based on results of matching
    Inputs
        - SQL: workflow.<uuid>
        - script: utils/identify_post_relationships_to_add.sql
        - script: utils/create_post_relationship_count.sql
        - script: utils/create_post_relationship.sql
    Outputs
        - stdout: SQL update script for core.post_relationship records (copy and run manually in the ministers database repo)
    Notes
        - The script generated in the write_add_posts_script.py step needs to be run before this script, so that all of the posts to which appointments are being updated exist
        - This relies on all MoS/PS/PUSS post names being in the form 'Minister for ...'
        - Compared to outputs of the scripts that add posts and update appointments, the output of this script needs more manual checking, as in some cases we want to merge or alter the group name which a post is attributed to by default
"""

import os

from ds_utils import database_operations as dbo
from ifg_ministers_database_utils.utils import extract_post_name_nouns
import pandas as pd

# %%
# SET CONSTANTS
RESERVED_TERMS = [
    "Foreign and Commonwealth Office",
    "Safe and Legal Migration",
    "Violence Against Women and Girls",
    "Yorkshire and the Humber",
]

# %%
# CONNECT TO D/B
connection = dbo.connect_sql_db(
    driver="pyodbc",
    driver_version=os.environ["ODBC_DRIVER"],
    dialect="mssql",
    server=os.environ["ODBC_SERVER"],
    database=os.environ["ODBC_DATABASE"],
    authentication=os.environ["ODBC_AUTHENTICATION"],
    username=os.environ["AZURE_CLIENT_ID"],
    password=os.environ["AZURE_CLIENT_SECRET"],
)

# %%
# READ IN SQL SCRIPTS
# Identify posts relationships to add
with open("govuk_data/appointments/utils/identify_post_relationships_to_add.sql", "r") as file:
    identify_post_relationships_to_add = file.read()

# Create post relationship count
with open("govuk_data/appointments/utils/create_post_relationship_count.sql", "r") as file:
    create_post_relationship_count = file.read()

# Create post relationship
with open("govuk_data/appointments/utils/create_post_relationship.sql", "r") as file:
    create_post_relationship = file.read()

# %%
# READ IN DATA TO USE IN SCRIPTS
df_post_relationships_to_add = pd.read_sql_query(
    sql=identify_post_relationships_to_add,
    con=connection,
)

# %%
# Identify post relationships to add
df_post_relationships_to_add = extract_post_name_nouns(
    df=df_post_relationships_to_add,
    reserved_terms=RESERVED_TERMS,
    post_name_col="post_name",
)
df_post_relationships_to_add = df_post_relationships_to_add.rename(
    columns={"name_nouns": "group_name"}
)

# %%
# Strip whitespace from group names
df_post_relationships_to_add["group_name"] = df_post_relationships_to_add[
    "group_name"
].str.strip()

# %%
# Escape single quotes in post names
df_post_relationships_to_add["post_name"] = df_post_relationships_to_add[
    "post_name"
].str.replace("'", "''")

# %%
# Escape single quotes in group names
df_post_relationships_to_add["group_name"] = df_post_relationships_to_add[
    "group_name"
].str.replace("'", "''")

# %%
# PRODUCE SCRIPT
add_posts_code = "--- SET HOLD\nset noexec on\n\n"

for index, row in df_post_relationships_to_add.iterrows():

    # Check if number of records affected is as expected
    add_posts_count_snippet = create_post_relationship_count.format(
        group_name=row["group_name"],
        post_name=row["post_name"],
        post_rank=row["post_rank"],
        organisation_short_name=row["organisation_short_name"],
        organisation_start_date=row["organisation_start_date"],
        organisation_end_date=row["organisation_end_date"],
    )
    add_posts_count_snippet = add_posts_count_snippet.replace(
        "= 'None'", "is null"
    ).replace(
        "= 'nan'", "is null"
    )

    assert pd.read_sql_query(
        sql=add_posts_count_snippet,
        con=connection,
    ).iloc[0, 0] == 1, (
        f"Expected 1 record to be affected, but {add_posts_count_snippet} affected {
            pd.read_sql_query(sql=add_posts_count_snippet, con=connection).iloc[0, 0]
        } records"
    )

    # Produce code
    add_posts_snippet = create_post_relationship.format(
        group_name=row["group_name"],
        post_name=row["post_name"],
        post_rank=row["post_rank"],
        organisation_short_name=row["organisation_short_name"],
        organisation_start_date=row["organisation_start_date"],
        organisation_end_date=row["organisation_end_date"],
    )
    add_posts_snippet = add_posts_snippet.replace(
        "= 'None'", "is null"
    ).replace(
        "= 'nan'", "is null"
    )

    add_posts_code += add_posts_snippet + "\n"

print(add_posts_code)

# %%
