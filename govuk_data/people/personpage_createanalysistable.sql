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
    cast(null as varchar(256)) post_name_clean,
    cast(null as varchar(128)) post_rank,
    0 is_on_leave,
    0 is_acting,
    cast(null as varchar(128)) leave_reason,
    [links.role_appointments.links.role.links.ordered_parent_organisations.content_id] organisation_id_govuk,
    [links.role_appointments.links.role.links.ordered_parent_organisations.title] organisation_name,
    cast(null as varchar(128)) organisation_name_clean,
	[links.role_appointments.links.role.links.ordered_parent_organisations.details.acronym] organisation_short_name,
	cast(null as varchar(128)) organisation_short_name_clean,
	cast([links.role_appointments.details.started_on] as date) appointment_start_date,
	cast([links.role_appointments.details.ended_on] as date) appointment_end_date
into [analysis].[ukgovt.minister_govuk_people_page_content_20240503]
from [source].[ukgovt.minister_govuk_people_page_content_20240503]
where
    -- Exclude duplicates introduced where a Welsh (cy) translation is available
    [links.available_translations.locale] = 'en' and

    -- Exclude non-ministerial roles (e.g. done before/after being a minister)
    [links.role_appointments.links.role.document_type] = 'ministerial_role' and

    -- Exclude roles we don't include in the min d/b
    [links.role_appointments.links.role.title] not in (
        'First Lord of the Treasury',
        'President of the Board of Trade'
    ) and

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
go


--- EDIT DATA
-- Drop appointments with a duration of one day or less
delete g
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] g
where
    datediff(day, g.appointment_start_date, g.appointment_end_date) <= 1


-- Fix one-off/uncommon issues with post_name
-- NB: post_id_govuk isn't updated as part of this cleaning
update g
set
    g.post_name_clean =
        case

            -- Fix capitalisation
            when g.post_name = 'Parliamentary Under Secretary of State for natural environment and science' then 'Parliamentary Under Secretary of State for Natural Environment and Science'
            when g.post_name = 'Parliamentary Under Secretary of State for water, forestry, rural affairs and resource management' then 'Parliamentary Under Secretary of State for Water, Forestry, Rural Affairs and Resource Management'
            when g.post_name = 'Parliamentary Under Secretary of State for farming, food and marine environment' then 'Parliamentary Under Secretary of State for Farming, Food and Marine Environment'

            -- Fix department-name-in-title denormalisation
            when g.post_name = 'Secretary of State for Ministry of Housing, Communities & Local Government' then 'Secretary of State for Housing, Communities & Local Government'
            when g.post_name = 'Parliamentary Under Secretary of State for BIS and DCMS and Minister for Intellectual Property' then 'Minister for Intellectual Property'
            when g.post_name = 'Parliamentary Under Secretary of State for Business, Innovation and Skills and Minister for Intellectual Property' then 'Minister for Intellectual Property'

            -- Formatting of whip roles
            when g.post_name = 'Assistant Government Whip' then 'Assistant Whip (HM Treasury)'
            when g.post_name = 'Baroness in Waiting (Government Whip)' then 'Baroness in Waiting'
            when g.post_name = 'Minister (Baroness in Waiting)' then 'Baroness in Waiting'
            when g.post_name = 'Spokesman and Whip in the House of Lords, Baroness in Waiting' then 'Baroness in Waiting'
            when g.post_name = 'Parliamentary Secretary to the Treasury (Chief Whip)' then 'Chief Whip and Parliamentary Secretary to the Treasury'
            when g.post_name = 'Comptroller of HM Household (Government Whip)' then 'Comptroller of HM Household (Senior Whip)'
            when g.post_name = 'Government Whip, Comptroller of HM Household' then 'Comptroller of HM Household (Senior Whip)'
            when g.post_name = 'Deputy Chief Whip, Comptroller of HM Household' then 'Comptroller of HM Household (Senior Whip)'
            when g.post_name = 'Government Whip (Lord Commissioner of HM Treasury)' then 'Lord Commissioner (Whip)'
            when g.post_name = 'Government Whip, Lord Commissioner of HM Treasury' then 'Lord Commissioner (Whip)'
            when g.post_name = 'Junior Lord of the Treasury (Government Whip)' then 'Lord Commissioner (Whip)'
            when g.person_name in ('Douglas Ross MP') and g.post_name = 'Government Whip' then 'Lord Commissioner (Whip)'
            when g.post_name = 'Lord in Waiting (Government Whip)' then 'Lord in Waiting'
            when g.post_name = 'Government Whip, Vice Chamberlain of HM Household' then 'Vice Chamberlain of HM Household (Senior Whip)'
            when g.post_name = 'Vice Chamberlain of HM Household (Government Whip)' then 'Vice Chamberlain of HM Household (Senior Whip)'

            -- Joint roles
            -- NB: Handled distinctly from other Parliamentary Secretary roles, as we require joint roles to be recorded under the same name at each department
            when g.post_name = 'Parliamentary Secretary (Minister for Defence People and Veterans)' then 'Minister for Defence People and Veterans'
            when g.post_name = 'Parliamentary Secretary (Minister for Equalities)' then 'Minister for Equalities'

            -- Fix miscellaneous cases
            when g.post_name = 'Commercial Secretary to the Treasury - Minister of State' then 'Commercial Secretary to the Treasury'
            when g.post_name = 'HM Advocate General for Scotland' then 'Advocate General for Scotland'
            when g.post_name = 'Parliamentary Under Secretary of State (Minister for Lords)' then 'Parliamentary Under Secretary of State'
            when g.post_name = 'Parliamentary Secretary of State (Deputy Leader of the House of Commons)' then 'Deputy Leader of the House of Commons'
            when g.person_name in ('Alun Cairns MP', 'Stephen Crabb MP', 'Guto Bebb', 'David Jones MP') and g.post_name = 'UK Government Minister for Wales' then 'Parliamentary Under Secretary of State'
            when g.post_name = 'Secretary of State for Business, Innovation and Skills and President of the Board of Trade' then 'Secretary of State for Business, Innovation and Skills'
            when g.post_name = 'Secretary of State for Communities and Local Government' then 'Secretary of State for Communities and Local Government'

            -- Base case
            else g.post_name
        end
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] g


-- Clean organisation_name
-- NB: organisation_id_govuk isn't updated as part of this cleaning
update g
set
    g.organisation_name_clean =
        case

            -- Consistency of whip roles with min d/b
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

            -- Missing organisation names
            when g.organisation_name is null and g.post_name = 'Minister of State' and g.person_name = 'Lord Howell of Guildford' then 'Foreign, Commonwealth & Development Office'
            when g.organisation_name is null and g.post_name = 'Minister on Leave (Secretary of State)' and g.person_name = 'Michelle Donelan MP' then 'Department for Science, Innovation and Technology'
            when g.organisation_name is null and g.post_name = 'Minister on Leave (Minister of State)' and g.person_name = 'Julia Lopez MP' then 'Department for Culture, Media and Sport'
            when g.organisation_name is null and g.post_name = 'Minister on Leave (Parliamentary Under Secretary of State)' and g.person_name = 'Baroness Penn' then 'Department for Levelling Up, Housing and Communities'
            when g.organisation_name is null and g.post_name = 'Parliamentary Under Secretary of State' and g.person_name = 'Nick Hurd' then 'Department for International Development'
            when g.organisation_name is null and g.post_name = 'Parliamentary Under Secretary of State for Sport and Civil Society' and g.person_name in ('Helen Grant MP', 'Tracey Crouch MP') then 'Department for Culture, Media and Sport'
            when g.organisation_name is null and g.post_name = 'Parliamentary Under Secretary of State for Women and Equalities' and g.person_name = 'Lynne Featherstone' then 'Department for Culture, Media and Sport'
            when g.organisation_name is null and g.post_name = 'Parliamentary Under Secretary of State for Women and Equalities' and g.person_name = 'Helen Grant MP' then 'Department for Culture, Media and Sport'
            when g.organisation_name is null and g.post_name = 'Minister for Women and Equalities' then 'Government Equalities Office'

            -- Base case
            else g.organisation_name
        end
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] g


-- Clean organisation_short_name
update g
set
    g.organisation_short_name_clean =
        case

            -- Missing organisation short names/consistency with min d/b
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

            -- Consistency of whip roles with min d/b
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

            -- Missing organisation short names
            when g.organisation_name is null and g.post_name = 'Minister of State' and g.person_name = 'Lord Howell of Guildford' then 'FCDO'
            when g.organisation_name is null and g.post_name = 'Minister on Leave (Secretary of State)' and g.person_name = 'Michelle Donelan MP' then 'DSIT'
            when g.organisation_name is null and g.post_name = 'Minister on Leave (Minister of State)' and g.person_name = 'Julia Lopez MP' then 'DCMS'
            when g.organisation_name is null and g.post_name = 'Minister on Leave (Parliamentary Under Secretary of State)' and g.person_name = 'Baroness Penn' then 'DLUHC'
            when g.organisation_name is null and g.post_name = 'Parliamentary Under Secretary of State' and g.person_name = 'Nick Hurd' then 'DfID'
            when g.organisation_name is null and g.post_name = 'Parliamentary Under Secretary of State for Sport and Civil Society' and g.person_name in ('Helen Grant MP', 'Tracey Crouch MP') then 'DCMS'
            when g.organisation_name is null and g.post_name = 'Parliamentary Under Secretary of State for Women and Equalities' and g.person_name = 'Lynne Featherstone' then 'DCMS'
            when g.organisation_name is null and g.post_name = 'Parliamentary Under Secretary of State for Women and Equalities' and g.person_name = 'Helen Grant MP' then 'DCMS'
            when g.organisation_name is null and g.post_name = 'Minister for Women and Equalities' then 'GEO'

            -- Base case
            else g.organisation_short_name
        end
from [analysis].[ukgovt.minister_govuk_people_page_content_20240503] g
