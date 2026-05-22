with source as (
    select * from {{ source('uea_raw', 'events') }}
)

select
    e.event_id,
    e.session_id,
    e.user_id,
    e.event_type,
    e.event_timestamp,
    date(e.event_timestamp) as event_date
from source e
join {{ ref('stg_sessions') }} s
    on e.session_id = s.session_id
where e.event_timestamp between s.session_start and s.session_end