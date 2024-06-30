update a
set
    a.post_id = t2.id
from core.person p
    inner join core.appointment a on
        p.id = a.person_id and
        isnull(p.start_date, '1900-01-01') <= a.start_date and
        p.end_date > a.start_date
    inner join core.appointment_characteristics ac on
        a.id = ac.appointment_id
    inner join core.post t1 on
        a.post_id = t1.id
    inner join core.post t2 on
        t2.name = '{post_name_new}' and
        t2.rank_equivalence = '{post_rank_new}'
    inner join core.organisation o1 on
        t1.organisation_id = o1.id and
        a.start_date >= isnull(o1.start_date, '1900-01-01') and
        a.end_date <= isnull(o1.end_date, '9999-12-31')
    inner join core.organisation o2 on
        t2.organisation_id = o2.id and
        o2.name = '{organisation_name}' and
        o2.short_name = '{organisation_short_name}' and
        ac.start_date >= isnull(o2.start_date, '1900-01-01') and
        ac.end_date <= isnull(o2.end_date, '9999-12-31')
where
    p.name = '{person_name}' and
    t1.name = '{post_name_old}' and
    t1.rank_equivalence = '{post_rank_old}' and
    o1.name = '{organisation_name}' and
    o1.short_name = '{organisation_short_name}' and
    ac.start_date = '{start_date}' and
    ac.end_date = '{end_date}'
