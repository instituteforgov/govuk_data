-- Identify post names to add and set post_rank
-- NB: This uses our organisation names, as we have greater confidence in these than in GOV.UK's,
-- but GOV.UK's post_rank (where not null) as in a small number of cases we are fixing the post rank
-- of an appointment
-- NB: This excludes appointments in the d/b matched to more than a single appointment in the
-- GOV.UK data - we handle these cases manually
select distinct
    w1.post_name_govuk post_name,
    w1.organisation_name_ifg organisation_name,
    w1.organisation_short_name_ifg organisation_short_name,
    case
        when w1.post_rank_govuk is null then w1.post_rank_ifg
        else w1.post_rank_govuk
    end post_rank
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
    ) and
    not exists (
        select *
        from core.post t
            inner join core.organisation o on
                t.organisation_id = o.id
        where
            w1.post_name_govuk = t.name and
            ((w1.post_rank_govuk is null and w1.post_rank_ifg = t.rank_equivalence) or (w1.post_rank_govuk = t.rank_equivalence)) and
            w1.organisation_name_ifg = o.name
    )
order by
    w1.post_name_govuk,
    w1.organisation_name_ifg,
    case
        when w1.post_rank_govuk is null then w1.post_rank_ifg
        else w1.post_rank_govuk
    end
