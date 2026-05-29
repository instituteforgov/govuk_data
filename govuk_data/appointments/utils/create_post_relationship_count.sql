select count(1)
from core.post t
    inner join core.organisation o on
        t.organisation_id = o.id
where
    t.name = '{post_name}' and
    t.rank_equivalence = '{post_rank}' and
    o.short_name = '{organisation_short_name}' and
    o.start_date = '{organisation_start_date}' and
    o.end_date = '{organisation_end_date}'
