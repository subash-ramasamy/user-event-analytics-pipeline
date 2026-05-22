with source as (
    select * from {{ source('uea_raw', 'sessions') }}
)

select
    session_id,
    user_id,
    session_start,
    session_end,
    device,
    timestamp_diff(session_end, session_start, second) as session_duration_seconds
from source
where session_end > session_start