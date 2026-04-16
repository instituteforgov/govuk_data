# GOV.UK people data

This project extracts data on individuals (identifiers and details of appointments) from GOV.UK and matches it to the IfG Ministers Database, producing SQL scripts to update the database.

## Related repositories

- [IfG Ministers Database - private repo](https://github.com/instituteforgov/ifg-ministers-database-private/): Holds the majority of code and resources for the IfG Ministers Database project (held privately)
- [IfG Ministers Database - public repo](https://github.com/instituteforgov/ifg-ministers-database-public/): The public part of the IfG Ministers Database project

## Directory structure

```
govuk_data/
└── people/
    ├── scrape_govuk_people.py
    ├── match_govuk_people.py
    ├── manage_data.sql
    ├── scrape_govuk_person_pages.py
    ├── personpage_qa.sql
    ├── personpage_createanalysistable.sql
    ├── clean_govuk_person_roles.py
    ├── match_govuk_appointments.py
    ├── personpage_reviewmatchoutput.sql
    ├── write_add_posts_script.py
    ├── write_update_appointments_script.py
    ├── data/
    │   └── df_person_page.pkl_20240503
    └── utils/
        ├── create_post_count.sql
        ├── create_post.sql
        ├── fuzzy_match.py
        ├── identify_appointments_to_edit.sql
        ├── identify_posts_to_add.sql
        ├── temp.py
        ├── update_appointment_count.sql
        ├── update_appointment.sql
        └── utils.py
```

## Database schemas

| Schema | Role |
| --- | --- |
| `core` | Core tables that make up the IfG Ministers Database — `person`, `appointment`, `post`, `organisation`, etc. Read-only from this pipeline's perspective |
| `source` | Raw data as scraped or ingested (written to in `scrape_govuk_people.py` and `scrape_govuk_person_pages.py`) |
| `reference` | Consolidated lookup tables used across runs (e.g. `reference.[ukgovt.govuk_strings_people]`, which is read by `match_govuk_people.py` and built up by `manage_data.sql`) |
| `analysis` | Processed and intermediate tables produced during matching and cleaning |

## Order in which to run scripts

| Script | Purpose |
| --- | --- |
| `scrape_govuk_people.py` | Scrape GOV.UK people strings (e.g. matthew-hancock) and save them to SQL |
| `match_govuk_people.py` | Read in post-2010 ministers and GOV.UK people strings, fuzzy match and manual match and save to SQL |
| `manage_data.sql` | Combine match results into a unified reference table of GOV.UK people strings |
| `scrape_govuk_person_pages.py` | Read in GOV.UK person page data from API endpoint |
| `personpage_qa.sql` | Explore source person page data ('EXPLORE DATA' section) |
| `personpage_createanalysistable.sql` | Create analysis table of person page data |
| `personpage_qa.sql` | QA analysis table of person page data ('QA data' section) |
| `clean_govuk_person_roles.py` | Clean GOV.UK person page data |
| `match_govuk_appointments.py` | Read in analysis table of GOV.UK appointments and match to ministers database |
| `personpage_reviewmatchoutput.sql` | Review output of manual review of possible matches |
| `write_add_posts_script.py` | Write script to add new posts based on results of matching |
| `<ministers-database>/editing_dataamendments.sql` | <Run output of write_add_posts_script.py> |
| `write_update_appointments_script.py` | Write script to update appointment records based on results of matching |
| `<ministers-database>/editing_dataamendments.py` | <Run output of write_update_appointments_script.py> |


## Environment variables

The following environment variables must be set before running any scripts:

| Variable | Description |
| --- | --- |
| `ODBC_DRIVER` | ODBC driver name |
| `ODBC_SERVER` | SQL Server hostname |
| `ODBC_DATABASE` | Database name |
| `ODBC_AUTHENTICATION` | Authentication method |
| `ODBC_USERNAME` | Database username |
