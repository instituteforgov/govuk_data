/***************************************************************************************************************************************************************************
    Purpose
      - Create reference table of gov.uk people strings
      - QA reference table
    Inputs
      - SQL: analysis.[ukgovt.minister_ids_govuk_strings_20211009]
      - SQL: analysis.[ukgovt.minister_ids_govuk_strings_202200702]
      - SQL: analysis.[ukgovt.minister_ids_govuk_strings_20240503]
    Outputs
      - SQL: reference.[ukgovt.govuk_strings_people]
    Parameters
      None
    Notes
      -- Based on an earlier script in Ministers/Gov.uk articles
***************************************************************************************************************************************************************************/



--- SET HOLD
set noexec on



--- CREATE REFERENCE TABLE, COMBINING ORIGINAL SOURCE TABLE AND SOURCE TABLE OF MANUAL ADDITIONS
drop table if exists reference.[ukgovt.govuk_strings_people]
select
    id,
    minister_name name,
    govuk_string
into reference.[ukgovt.govuk_strings_people]
from analysis.[ukgovt.minister_ids_govuk_strings_20211009]

union

select *
from analysis.[ukgovt.minister_ids_govuk_strings_202200702]

union

select *
from analysis.[ukgovt.minister_ids_govuk_strings_20240503]



--- QA
-- Duplicate names
select
    s.name
from reference.[ukgovt.govuk_strings_people] s
group by
    s.name
having
    count(1) > 1

select *
from reference.[ukgovt.govuk_strings_people] s
where
    s.name in (
        'Andrew Mitchell',
        'John Randall',
        'Lord Howell of Guildford'
    )
order by
    s.name

delete s
from reference.[ukgovt.govuk_strings_people] s
where
    s.govuk_string in (
        'andrew-mitchell--2',
        'john-randall--2'
    )

