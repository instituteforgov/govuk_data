-- Review records with no matches
select
    w1.reviewed,
    w1.match_accepted,
    w1.replace_post_name,
    w1.notes,
    w1.appointment_id_ifg,
    w1.person_name_ifg,
    w1.post_name_ifg,
    -- w1.post_rank_ifg,
    -- w1.organisation_name_ifg,
    w1.organisation_short_name_ifg,
    -- w1.cabinet_status,
    -- w1.is_on_leave_ifg,
    -- w1.is_acting_ifg,
    -- w1.leave_reason_ifg,
    w1.start_date_ifg,
    w1.end_date_ifg,
    w1.post_name_govuk,
    -- w1.post_rank_govuk,
    -- w1.organisation_name_govuk,
    w1.organisation_short_name_govuk,
    -- w1.is_on_leave_govuk,
    -- w1.is_acting_govuk,
    -- w1.leave_reason_govuk,
    w1.start_date_govuk,
    w1.end_date_govuk,
    w1.organisation_short_name_match,
    w1.post_name_match,
    w1.start_date_match,
    w1.end_date_match,
    w1.date_match,
    w1.match_score
from workflow.[50556707-3276-404a-8a3f-cee24d329bae] w1
where
    w1.reviewed = 1 and
    not exists (
        select *
        from workflow.[50556707-3276-404a-8a3f-cee24d329bae] w2
        where
            w2.match_accepted = 1 and
            w1.appointment_id_ifg = w2.appointment_id_ifg
    )
order by
    w1.person_name_ifg,
    w1.appointment_id_ifg,
    w1.match_score


-- Review records matched to more than a single post_name_govuk
-- NB: Ignoring women/equalities ministers - what we consider to have been a single appt is
-- sometimes recorded under more than one post name on GOV.UK
select
    w1.reviewed,
    w1.match_accepted,
    w1.replace_post_name,
    w1.notes,
    w1.appointment_id_ifg,
    w1.person_name_ifg,
    w1.post_name_ifg,
    -- w1.post_rank_ifg,
    -- w1.organisation_name_ifg,
    w1.organisation_short_name_ifg,
    -- w1.cabinet_status,
    -- w1.is_on_leave_ifg,
    -- w1.is_acting_ifg,
    -- w1.leave_reason_ifg,
    w1.start_date_ifg,
    w1.end_date_ifg,
    w1.post_name_govuk,
    -- w1.post_rank_govuk,
    -- w1.organisation_name_govuk,
    w1.organisation_short_name_govuk,
    -- w1.is_on_leave_govuk,
    -- w1.is_acting_govuk,
    -- w1.leave_reason_govuk,
    w1.start_date_govuk,
    w1.end_date_govuk,
    -- w1.organisation_short_name_match,
    -- w1.post_name_match,
    -- w1.start_date_match,
    -- w1.end_date_match,
    -- w1.date_match,
    w1.match_score
from workflow.[50556707-3276-404a-8a3f-cee24d329bae] w1
where
    w1.reviewed = 1 and
    w1.match_accepted = 1 and
    exists (
        select
            w2.appointment_id_ifg,
            count(distinct w2.post_name_govuk)
        from workflow.[50556707-3276-404a-8a3f-cee24d329bae] w2
        where
            w1.appointment_id_ifg = w2.appointment_id_ifg and
            w2.match_accepted = 1 and
            w2.post_name_ifg not in (
                'Minister for Women',
                'Minister for Equalities',
                'Minister for Women and Equalities',
                'Minister of State for Women and Equalities',
                'Parliamentary Under Secretary of State for Women and Equalities'
            )
        group by
            w2.appointment_id_ifg
        having
            count(distinct w2.post_name_govuk) > 1
    )
order by
    w1.person_name_ifg,
    w1.appointment_id_ifg,
    w1.start_date_govuk,
    w1.end_date_govuk


-- Review notes
select
    w1.reviewed,
    w1.match_accepted,
    w1.replace_post_name,
    w1.notes,
    w1.appointment_id_ifg,
    w1.person_name_ifg,
    w1.post_name_ifg,
    -- w1.post_rank_ifg,
    -- w1.organisation_name_ifg,
    w1.organisation_short_name_ifg,
    -- w1.cabinet_status,
    -- w1.is_on_leave_ifg,
    -- w1.is_acting_ifg,
    -- w1.leave_reason_ifg,
    w1.start_date_ifg,
    w1.end_date_ifg,
    w1.post_name_govuk,
    -- w1.post_rank_govuk,
    -- w1.organisation_name_govuk,
    w1.organisation_short_name_govuk,
    -- w1.is_on_leave_govuk,
    -- w1.is_acting_govuk,
    -- w1.leave_reason_govuk,
    w1.start_date_govuk,
    w1.end_date_govuk,
    -- w1.organisation_short_name_match,
    -- w1.post_name_match,
    -- w1.start_date_match,
    -- w1.end_date_match,
    -- w1.date_match,
    w1.match_score
from workflow.[50556707-3276-404a-8a3f-cee24d329bae] w1
where
    w1.reviewed = 1 and
    w1.notes is not null
order by
    w1.person_name_ifg,
    w1.appointment_id_ifg,
    w1.match_score
