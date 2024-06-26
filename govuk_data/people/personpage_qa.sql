--- EXPLORE DATA
-- Non-ministerial roles
select
    [details.full_name],
    [links.role_appointments.links.role.title],
    [links.role_appointments.links.role.document_type],
    *
from [source].[ukgovt.minister_govuk_people_page_content_20240503]
where
    [links.role_appointments.links.role.document_type] != 'ministerial_role'


-- Are all Cabinet Office Board appointments duplicates of Cabinet Office appointments?
select *
from [source].[ukgovt.minister_govuk_people_page_content_20240503] t1
where
    t1.[links.role_appointments.links.role.links.ordered_parent_organisations.title] = 'Cabinet Office Board' and
    not exists (
        select *
        from [source].[ukgovt.minister_govuk_people_page_content_20240503] t2
        where
            t1.[links.role_appointments.content_id] = t2.[links.role_appointments.content_id] and
            t2.[links.role_appointments.links.role.links.ordered_parent_organisations.title] = 'Cabinet Office'
    )


-- Are all Disability Unit/Equality Unit/Race Disparity Unit appointments duplicates of GEO appointments?
select *
from [source].[ukgovt.minister_govuk_people_page_content_20240503] t1
where
    t1.[links.role_appointments.links.role.links.ordered_parent_organisations.title] in (
        'Disability Unit',
        'Equality Hub',
        'Race Disparity Unit'
    ) and
    not exists (
        select *
        from [source].[ukgovt.minister_govuk_people_page_content_20240503] t2
        where
            t1.[links.role_appointments.content_id] = t2.[links.role_appointments.content_id] and
            t2.[links.role_appointments.links.role.links.ordered_parent_organisations.title] = 'Government Equalities Office'
    )


--- QA data
-- Appointments with a duration of one day or less
select
    *
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503]
where
    datediff(day, appointment_start_date, appointment_end_date) <= 1
order by
    person_name


-- Check for complete duplicates
drop table if exists #complete_duplicates;
select
    person_id,
    person_name,
    appointment_id_govuk,
    post_name,
    organisation_name,
    organisation_short_name,
    appointment_start_date,
    appointment_end_date,
    count(1) count
into #complete_duplicates
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503]
group by
    person_id,
    person_name,
    appointment_id_govuk,
    post_name,
    organisation_name,
    organisation_short_name,
    appointment_start_date,
    appointment_end_date
having
    count(1) > 1

select
    person_name,
    post_name,
    organisation_name,
    appointment_id_govuk,
    appointment_start_date,
    appointment_end_date
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] t
where
    exists (
        select *
        from #complete_duplicates d
        where
            t.appointment_id_govuk = d.appointment_id_govuk
    )
order by
    appointment_id_govuk,
    organisation_name


-- Check for records that share a GOV.UK appointment ID
-- NB: In the GOV.UK data, joint appointments share an appointment ID - these
-- will show as genuine duplicates here
drop table if exists #duplicates;
select
    appointment_id_govuk,
    count(1) count
into #duplicates
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503]
group by
    appointment_id_govuk
having
    count(1) > 1

select
    person_name,
    post_name,
    organisation_name,
    appointment_id_govuk,
    appointment_start_date,
    appointment_end_date
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] t
where
    exists (
        select *
        from #duplicates d
        where
            t.appointment_id_govuk = d.appointment_id_govuk
    )
order by
    appointment_id_govuk,
    organisation_name
