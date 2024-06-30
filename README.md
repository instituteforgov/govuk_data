## Order in which to run scripts
| Script | Purpose |
| ----------- | ----------- |
| `scrape_govuk_people.py` | Scrape GOV.UK people strings (e.g. matthew-hancock) and save them to SQL |
| `match_govuk_people.py` | Read in post-2010 ministers and GOV.UK people strings, fuzzy match and manual match and save to SQL |
| `scrape_govuk_person_pages.py` | Read in GOV.UK person page data from API endpoint |
| `personpage_qa.sql` | Explore and QA person page data |
| `personpage_createanalysistable.sql` | Create analysis table of person page data |
| `personpage_qa.sql` | Explore and QA person page data |
| `clean_govuk_person_roles.py` | Clean GOV.UK person page data |
| `match_govuk_appointments.py` | Read in analysis table of GOV.UK appointments and match to ministers database |
| `personpage_reviewmatchoutput.sql` | Review output of manual review of possible matches |
| `write_add_posts_script.py` | Write script to add new posts based on results of matching |
| `<ministers-database>/editing_dataamendments.sql` | <Run output of write_add_posts_script.py> |
| `write_update_appointments_script.py` | Write script to update appointment records based on results of matching |
| `<ministers-database>/editing_dataamendments.py` | <Run output of write_update_appointments_script.py> |
