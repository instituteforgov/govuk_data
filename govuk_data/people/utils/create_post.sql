insert into core.post (id, organisation_id, name, rank_equivalence)
select
    newid(),
    o.id,
    '{post_name}',
    '{post_rank}'
from core.organisation o
where
    o.name = '{organisation_name}' and
    o.short_name = '{organisation_short_name}' and
    o.start_date = '{organisation_start_date}' and
    o.end_date = '{organisation_end_date}'
