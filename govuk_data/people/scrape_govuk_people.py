# %%
# #!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Purpose
        Scrape gov.uk people strings (e.g. matthew-hancock) and save them to SQL
    Inputs
        - Web: gov.uk pages
    Outputs
        - SQL: source.ukgovt.govuk_strings_people_20240503
    Parameters
        None
    Notes
        None
'''

import os
import requests
import uuid
import urllib

from bs4 import BeautifulSoup
import pandas as pd
import sqlalchemy
from sqlalchemy.dialects.mssql import UNIQUEIDENTIFIER

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
# SCRAPE DATA AND SAVE TO DATAFRAME
base_url = 'https://www.gov.uk/'
rows_list = []

next_page = urllib.parse.urljoin(base_url, 'government/people?page=1')

while next_page:
    r = requests.get(next_page)
    soup = BeautifulSoup(r.content, features='html.parser')

    people_ul_list = soup.find('ul', 'gem-c-document-list')

    for person in people_ul_list.find_all('li'):
        dict = {}
        dict.update({
            'govuk_ga_id': person.a['data-ga4-ecommerce-content-id'],
            'name': person.a.text,
            'href': person.a['href'],
        })
        rows_list.append(dict)

    if soup.find('div', 'govuk-pagination__next'):
        next_page = soup.find('div', 'govuk-pagination__next').a['href']
        next_page = urllib.parse.urljoin(base_url, next_page)
    else:
        next_page = None

df_govuk_person = pd.DataFrame(rows_list)

# %%
# RUN CHECKS
# Check that IDs and URLs contain unique values
# NB: The same will not be true of names - there are both legitimate and erroneous duplicates
assert df_govuk_person['id'].nunique() == df_govuk_person.shape[0]
assert df_govuk_person['href'].nunique() == df_govuk_person.shape[0]

# %%
# Check that all URls take the form /government/people/<something>
assert all(df_govuk_person['href'].str.startswith('/government/people/'))

# %%
# EDIT DATA
# Add our own ID column
df_govuk_person.insert(0, 'id', [uuid.uuid4() for _ in range(len(df_govuk_person))])

# %%
# Pull name string out of URL
df_govuk_person['govuk_string'] = df_govuk_person['href'].str.extract(r'/government/people/(.*)')

# %%
# SAVE RESULTS TO SQL
# Get max length of name and govuk_string
max_name_length = df_govuk_person['name'].str.len().max()
max_govuk_string_length = df_govuk_person['govuk_string'].str.len().max()

# %%
# Save data
df_govuk_person[['id', 'name', 'govuk_string']].to_sql(
    'ukgovt.govuk_strings_people_20240503',
    schema='source',
    con=connection,
    dtype={
        'id': UNIQUEIDENTIFIER,
        'name': sqlalchemy.types.NVARCHAR(length=max_name_length),
        'govuk_string': sqlalchemy.types.NVARCHAR(length=max_govuk_string_length)
    },
    index=False,
    if_exists='replace'
)

# %%
