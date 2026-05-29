insert into core.post_relationship (id, post_id, group_name, group_seniority)
select
    newid(),
    t.id,
    '{group_name}',
    case
        when t.rank_equivalence in ('MoS', 'PUSS') then 'MoS/PUSS'
        else t.rank_equivalence
    end
from core.post t
    inner join core.organisation o on
        t.organisation_id = o.id
where
    t.name = '{post_name}' and
    t.rank_equivalence = '{post_rank}' and
    o.short_name = '{organisation_short_name}' and
    o.start_date = '{organisation_start_date}' and
    o.end_date = '{organisation_end_date}'
