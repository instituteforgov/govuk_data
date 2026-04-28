# GOV.UK people data

This project extracts data on individuals (identifiers and details of appointments) from GOV.UK and matches it to the IfG Ministers Database, producing SQL scripts to update the database.

## Related repositories

- 🔒 [IfG Ministers Database - private repo](https://github.com/instituteforgov/ifg-ministers-database-private/): Holds the majority of code and resources for the IfG Ministers Database project (held privately). Appointment information collated in this repo is matched to IfG Ministers Database appointments data and scripts generated to update the data held in the database
- 🔓 [IfG Ministers Database - public repo](https://github.com/instituteforgov/ifg-ministers-database-public/): The public part of the IfG Ministers Database project

## Project structure

```
├── govuk_data/
|   ├── people_strings/
|   |   ├── scrape_govuk_people.py
|   |   ├── match_govuk_people.py
|   |   ├── build_people_strings_reference.sql
|   |   └── data/
|   |       └── match_<datestamp>.xlsx
|   ├── appointments/
|   |   ├── extract_govuk_person_pages.py
|   |   ├── personpage_qa_source.sql
|   |   ├── personpage_createanalysistable.sql
|   |   ├── personpage_qa_analysis.sql
|   |   ├── clean_govuk_person_roles.py
|   |   ├── match_govuk_appointments.py
|   |   ├── personpage_reviewmatchoutput.sql
|   |   ├── write_add_posts_script.py
|   |   ├── write_update_appointments_script.py
|   |   ├── data/
|   |   │   └── df_person_page.pkl_<datestamp>
|   |   └── utils/
|   |       ├── create_post_count.sql
|   |       ├── create_post.sql
|   |       ├── identify_appointments_to_edit.sql
|   |       ├── identify_posts_to_add.sql
|   |       ├── update_appointment_count.sql
|   |       ├── update_appointment.sql
|   |       └── utils.py
|   └── utils/
|       └── fuzzy_match.py
.gitignore
.pre-commit-config.yaml
README.md
```

## Database schemas

| Schema | Role |
| --- | --- |
| `core` | Core tables that make up the IfG Ministers Database — `person`, `appointment`, `post`, `organisation`, etc. Read-only from this pipeline's perspective |
| `source` | Raw data as scraped or extracted from GOV.UK, written by `people_strings/scrape_govuk_people.py` and `appointments/extract_govuk_person_pages.py` |
| `reference` | Consolidated lookup tables used across runs, built up by `build_people_strings_reference.sql` |
| `analysis` | Processed and intermediate tables produced during matching and cleaning |
| `workflow` | Ephemeral per-run matching tables written by `match_govuk_appointments.py`; a new UUID-named table is created each run |

## People strings pipeline

Run once per data pull to build up the `reference.[ukgovt.govuk_strings_people]` lookup, which maps IfG minister IDs to their GOV.UK people string (e.g. `matthew-hancock`). Only ministers not already in the reference table need to be matched each run.

| Step | Script | Inputs | Outputs |
| --- | --- | --- | --- |
| 1 | `scrape_govuk_people.py` | Web: gov.uk/government/people (paginated) | `source.[ukgovt.govuk_strings_people_<datestamp>]` |
| 2 | `match_govuk_people.py` | <ul><li>`core.person`</li><li>`core.appointment`</li><li>`reference.[ukgovt.govuk_strings_people]`</li><li>`source.[ukgovt.govuk_strings_people_<datestamp>]`</li><li>`data/match_<datestamp>.xlsx` — **Following manual review**</li></ul> | <ul><li>`data/match_<datestamp>.xlsx`</li><li>`analysis.[ukgovt.minister_ids_govuk_strings_<datestamp>]`</li></ul> |
| 3 | `build_people_strings_reference.sql` | `analysis.[ukgovt.minister_ids_govuk_strings_<datestamp>]` (one table per historical run, unioned) | `reference.[ukgovt.govuk_strings_people]` |

## Appointments pipeline

Run once per data pull to match GOV.UK appointment records to the IfG Ministers Database and generate SQL scripts to update it.

| Step | Script | Inputs | Outputs |
| --- | --- | --- | --- |
| 1 | `extract_govuk_person_pages.py` | <ul><li>`reference.[ukgovt.govuk_strings_people]`</li><li>GOV.UK Content API</li></ul> | <ul><li>`data/df_person_page.pkl_<datestamp>` (checkpoint)</li><li>`source.[ukgovt.minister_govuk_people_page_content_<datestamp>]`</li></ul> |
| 2 | `personpage_qa_source.sql` | `source.[ukgovt.minister_govuk_people_page_content_<datestamp>]` | *(exploratory — no outputs; findings inform filters in step 3)* |
| 3 | `personpage_createanalysistable.sql` | `source.[ukgovt.minister_govuk_people_page_content_<datestamp>]` | `analysis.[ukgovt.minister_govuk_people_page_content_<datestamp>]` |
| 4 | `personpage_qa_analysis.sql` | `analysis.[ukgovt.minister_govuk_people_page_content_<datestamp>]` | *(QA — no outputs)* |
| 5 | `clean_govuk_person_roles.py` | `analysis.[ukgovt.minister_govuk_people_page_content_<datestamp>]` | `analysis.[ukgovt.minister_govuk_people_page_content_<datestamp>]` *(updated in place)* |
| 6 | `match_govuk_appointments.py` | <ul><li>`analysis.[ukgovt.minister_govuk_people_page_content_<datestamp>]`</li><li>`core.person`</li><li>`core.appointment`</li><li>`core.appointment_characteristics`</li><li>`core.post`</li><li>`core.organisation`</li></ul> | `workflow.<uuid>` *(UUID printed to console — substitute into steps 7–9)* |
| 7 | `personpage_reviewmatchoutput.sql` | `workflow.<uuid>` | *(manual review — no outputs; update `reviewed`/`match_accepted`/`replace_post_name` flags in the workflow table)* |
| 8 | `write_add_posts_script.py` | `workflow.<uuid>` (via `utils/identify_posts_to_add.sql`) | stdout: SQL to insert new records into `core.post` — **copy and run manually in the IfG Ministers Database** |
| 9 | `write_update_appointments_script.py` | `workflow.<uuid>` (via `utils/identify_appointments_to_edit.sql`) | stdout: SQL to update `core.appointment` post IDs — **copy and run manually in the IfG Ministers Database** |

## Environment variables

The following environment variables must be set before running any scripts:

| Variable | Description |
| --- | --- |
| `ODBC_DRIVER` | ODBC driver name |
| `ODBC_SERVER` | SQL Server hostname |
| `ODBC_DATABASE` | Database name |
| `ODBC_AUTHENTICATION` | Authentication method |
| `ODBC_USERNAME` | Database username |

## Contributing

This project uses `pre-commit` hooks to ensure code quality. To set up:
 
1. Install `pre-commit` on your system if you don't already have it:
 
    ```bash
    pip install pre-commit
    ```
 
1. Set up `pre-commit` in your copy of this project. In the project directory, run:
    ```bash
    pre-commit install
    ```
 
Rules that are applied can be found in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).
 
The hooks run automatically on commit, or manually with `pre-commit run --all-files`.
