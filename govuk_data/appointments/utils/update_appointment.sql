update a
set
    a.post_id = t2.id
from core.appointment a
    inner join core.appointment_characteristics ac on
        a.id = ac.appointment_id
    inner join core.person p on
        a.person_id = p.id and
        a.start_date >= isnull(p.start_date, '1900-01-01') and
        a.start_date < isnull(p.end_date, '9999-12-31')
    inner join core.post t1 on
        a.post_id = t1.id
    inner join core.post t2 on
        t2.name = '{post_name_new}' and
        t2.rank_equivalence = '{post_rank_new}'
    inner join core.organisation o1 on
        t1.organisation_id = o1.id and
        a.start_date >= isnull(o1.start_date, '1900-01-01') and
        isnull(a.end_date, '9999-12-31') <= isnull(o1.end_date, '9999-12-31')
    inner join core.organisation o2 on
        t2.organisation_id = o2.id and
        o2.short_name = '{organisation_short_name}' and
        ac.start_date >= isnull(o2.start_date, '1900-01-01') and
        isnull(ac.end_date, '9999-12-31') <= isnull(o2.end_date, '9999-12-31')
where
    p.name = '{person_name}' and
    t1.name = '{post_name_old}' and
    t1.rank_equivalence = '{post_rank_old}' and
    o1.short_name = '{organisation_short_name}' and
    ac.start_date = '{start_date}' and
    ac.end_date = '{end_date}'
