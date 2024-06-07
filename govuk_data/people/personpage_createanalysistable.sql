--- SET HOLD
set noexec on



--- CREATE WORKING VERSIONS OF TABLES
-- Create slimmed down table
-- NB: This applies distinct, as there are otherwise erroneously some
-- duplicates, owing to errors in the source data
drop table if exists [analysis].[ukgovt.minister_govuk_people_page_content_20240503]
select distinct
    [ifg_person_id] person_id,
    [content_id] person_id_govuk,
	[details.full_name] person_name,
	[links.role_appointments.content_id] appointment_id_govuk,
    [links.role_appointments.links.role.content_id] post_id_govuk,
	[links.role_appointments.links.role.title] post_name,
    [links.role_appointments.links.role.links.ordered_parent_organisations.content_id] organisation_id_govuk,
    [links.role_appointments.links.role.links.ordered_parent_organisations.title] organisation_name,
	[links.role_appointments.links.role.links.ordered_parent_organisations.details.acronym] organisation_short_name,
	cast([links.role_appointments.details.started_on] as date) appointment_start_date,
	cast([links.role_appointments.details.ended_on] as date) appointment_end_date
into [analysis].[ukgovt.minister_govuk_people_page_content_20240503]
from [source].[ukgovt.minister_govuk_people_page_content_20240503]
where
    -- Exclude duplicates introduced where a Welsh (cy) translation is available
    [links.available_translations.locale] = 'en' and

    -- Exclude non-ministerial roles (e.g. done before/after being a minister)
    [links.role_appointments.links.role.document_type] = 'ministerial_role' and

    -- Restrict to departments
    -- NB: This does drop a small number of Disability Unit/Equality Unit/Race Disparity Unit that aren't
    -- duplicates of GEO records. But in all cases there is a department-proper record that we're retaining
    (
        [links.role_appointments.links.role.links.ordered_parent_organisations.analytics_identifier] is null or
        [links.role_appointments.links.role.links.ordered_parent_organisations.analytics_identifier] like 'd%' or
        [links.role_appointments.links.role.links.ordered_parent_organisations.title] in (
            'Deputy Prime Minister''s Office',
            'Government Equalities Office',
            'Prime Minister''s Office, 10 Downing Street'
        )
    ) and
    (
        [links.role_appointments.links.role.links.ordered_parent_organisations.title] is null or
        [links.role_appointments.links.role.links.ordered_parent_organisations.title] not in (
            'UK Export Finance',
            'UK Trade & Investment'
        )
    )



--- EDIT DATA
-- Clean organisation_name
update g
set
    g.organisation_name =
        case
            when g.post_name in (
                'Assistant Government Whip',
                'Assistant Whip',
                'Comptroller of HM Household (Government Whip) ',
                'Deputy Chief Whip, Comptroller of HM Household',
                'Government Whip',
                'Government Whip, Comptroller of HM Household',
                'Government Whip (Lord Commissioner of HM Treasury)',       -- Sic
                'Government Whip, Lord Commissioner of HM Treasury',        -- Sic
                'Government Whip, Vice Chamberlain of HM Household',
                'Junior Lord of the Treasury (Government Whip)',        -- Sic
                'Parliamentary Secretary to the Treasury (Chief Whip)',
                'Treasurer of HM Household (Deputy Chief Whip)',
                'Vice Chamberlain of HM Household (Government Whip)'
            ) then 'Government Whips-House of Commons'
            when g.post_name in (
                'Baroness in Waiting (Government Whip)',
                'Captain of the Honourable Corps of Gentlemen at Arms (Lords Chief Whip)',
                'Captain of the King''s Bodyguard of the Yeomen of the Guard (Lords Deputy Chief Whip)',
                'Lord in Waiting (Government Whip) ',
                'Lord in Waiting',
                'Spokesman and Whip in the House of Lords, Baroness in Waiting'
            ) then 'Government Whips-House of Lords'
            else g.organisation_name
        end
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] g


-- Clean organisation_short_name
update g
set
    g.organisation_short_name =
        case
            when g.organisation_name = 'Cabinet Office' then 'CO'
            when g.organisation_name = 'Department for Digital, Culture, Media & Sport' then 'DCMS'
            when g.organisation_name = 'Deputy Prime Minister''s Office' then 'DPM'
            when g.organisation_name = 'Home Office' then 'HO'
            when g.organisation_name = 'Office of the Leader of the House of Commons' then 'Leader Commons'
            when g.organisation_name = 'Office of the Leader of the House of Lords' then 'Leader Lords'
            when g.organisation_name = 'Prime Minister''s Office, 10 Downing Street' then 'PM'
            when g.organisation_name = 'Office of the Secretary of State for Scotland' then 'Scot'
            when g.organisation_name = 'Office of the Secretary of State for Wales' then 'Wal'
            when g.organisation_short_name = 'DFID' then 'DfID'
            when g.organisation_short_name = 'MOD' then 'MoD'
            when g.organisation_short_name = 'MOJ' then 'MoJ'
            when g.post_name in (
                'Assistant Government Whip',
                'Assistant Whip',
                'Comptroller of HM Household (Government Whip) ',
                'Deputy Chief Whip, Comptroller of HM Household',
                'Government Whip',
                'Government Whip, Comptroller of HM Household',
                'Government Whip (Lord Commissioner of HM Treasury)',        -- Sic
                'Government Whip, Lord Commissioner of HM Treasury',        -- Sic
                'Government Whip, Vice Chamberlain of HM Household',
                'Junior Lord of the Treasury (Government Whip)',        -- Sic
                'Parliamentary Secretary to the Treasury (Chief Whip)',
                'Treasurer of HM Household (Deputy Chief Whip)',
                'Vice Chamberlain of HM Household (Government Whip)'
            ) then 'Whip Commons'
            when g.post_name in (
                'Baroness in Waiting (Government Whip)',
                'Captain of the Honourable Corps of Gentlemen at Arms (Lords Chief Whip)',
                'Captain of the King''s Bodyguard of the Yeomen of the Guard (Lords Deputy Chief Whip)',
                'Lord in Waiting (Government Whip) ',
                'Lord in Waiting',
                'Spokesman and Whip in the House of Lords, Baroness in Waiting'
            ) then 'Whip Lords'
            else g.organisation_short_name
        end
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] g