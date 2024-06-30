select count(1)
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
    inner join core.organisation o on
        t1.organisation_id = o.id
where
    p.name = '{person_name}' and
    t1.name = '{post_name_old}' and
    t1.rank_equivalence = '{post_rank_old}' and
    o.name = '{organisation_name}' and
    o.short_name = '{organisation_short_name}' and
    a.start_date = '{start_date}' and
    a.end_date = '{end_date}'
