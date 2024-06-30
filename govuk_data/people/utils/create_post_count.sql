select count(1)
from core.organisation o
where
    o.name = '{organisation_name}' and
    o.short_name = '{organisation_short_name}' and
    o.start_date = '{organisation_start_date}' and
    o.end_date = '{organisation_end_date}'
