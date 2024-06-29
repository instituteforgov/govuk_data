-- Identify appointments for which we want to change the post
-- NB: This excludes appointments in the d/b matched to more than a single appointment in the
-- GOV.UK data - we handle these cases manually
select
    w1.appointment_id_ifg appointment_id,
    w1.person_name_ifg person_name,
    w1.post_name_ifg post_name_old,
    w1.post_name_govuk post_name_new,
    w1.organisation_name_ifg organisation_name,
    w1.organisation_short_name_ifg organisation_short_name,
    w1.post_rank_ifg post_rank_old,
    case
        when w1.post_rank_govuk is null then w1.post_rank_ifg
        else w1.post_rank_govuk
    end post_rank_new,
    w1.start_date_ifg start_date,
    w1.end_date_ifg end_date
from workflow.[50556707-3276-404a-8a3f-cee24d329bae] w1
where
    w1.reviewed = 1 and
    w1.match_accepted = 1 and
    w1.replace_post_name = 1 and
    not exists (
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
    w1.start_date_ifg,
    w1.end_date_ifg,
    w1.post_name_govuk,
    w1.organisation_name_ifg,
    case
        when w1.post_rank_govuk is null then w1.post_rank_ifg
        else w1.post_rank_govuk
    end
