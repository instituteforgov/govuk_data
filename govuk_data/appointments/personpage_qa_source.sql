/***************************************************************************************************************************************************************************
    Purpose
      - Explore raw (source) GOV.UK person page data prior to creating the analysis table
      - Findings inform the filtering and deduplication logic applied in
        personpage_createanalysistable.sql
    Inputs
      - SQL: source.[ukgovt.minister_govuk_people_page_content_20260428]
    Outputs
      None
    Parameters
      None
    Notes
      - Run before personpage_createanalysistable.sql
***************************************************************************************************************************************************************************/



--- EXPLORE DATA
-- Non-ministerial roles
select
    umgppc.[details.full_name],
    umgppc.[links.role_appointments.links.role.title],
    umgppc.[links.role_appointments.links.role.document_type],
    umgppc.*
from [source].[ukgovt.minister_govuk_people_page_content_20260428] umgppc
where
    umgppc.[links.role_appointments.links.role.document_type] != 'ministerial_role'
order by
    umgppc.[links.role_appointments.links.role.document_type],
    umgppc.[details.full_name],
    umgppc.[links.role_appointments.links.role.title]


-- Are all Cabinet Office Board appointments duplicates of Cabinet Office appointments?
select *
from [source].[ukgovt.minister_govuk_people_page_content_20260428] t1
where
    t1.[links.role_appointments.links.role.links.ordered_parent_organisations.title] = 'Cabinet Office Board' and
    not exists (
        select *
        from [source].[ukgovt.minister_govuk_people_page_content_20260428] t2
        where
            t1.[links.role_appointments.content_id] = t2.[links.role_appointments.content_id] and
            t2.[links.role_appointments.links.role.links.ordered_parent_organisations.title] = 'Cabinet Office'
    )


-- Are all Disability Unit/Equality Unit/Race Disparity Unit appointments duplicates of GEO appointments?
select *
from [source].[ukgovt.minister_govuk_people_page_content_20260428] t1
where
    t1.[links.role_appointments.links.role.links.ordered_parent_organisations.title] in (
        'Disability Unit',
        'Equality Hub',
        'Race Disparity Unit'
    ) and
    not exists (
        select *
        from [source].[ukgovt.minister_govuk_people_page_content_20260428] t2
        where
            t1.[links.role_appointments.content_id] = t2.[links.role_appointments.content_id] and
            t2.[links.role_appointments.links.role.links.ordered_parent_organisations.title] = 'Government Equalities Office'
    )
