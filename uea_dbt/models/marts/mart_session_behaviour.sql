-- Business Question: How do users behave within sessions?
-- Metrics: Session duration, event counts, device usage per session

with sessions as (
    select * from {{ ref('stg_sessions') }}
),

events as (
    select * from {{ ref('stg_events') }}
),

session_events as (
    select
        s.session_id,
        s.user_id,
        s.device,
        s.session_start,
        s.session_end,
        s.session_duration_seconds,
        count(e.event_id)                           as total_events,
        countif(e.event_type = 'order_placed')      as orders_in_session,
        countif(e.event_type = 'payment_failed')    as payment_failures,
        countif(e.event_type = 'order_dropped')     as order_drops
    from sessions s
    left join events e on s.session_id = e.session_id
    group by
        s.session_id,
        s.user_id,
        s.device,
        s.session_start,
        s.session_end,
        s.session_duration_seconds
)

select
    session_id,
    user_id,
    device,
    session_start,
    session_end,
    session_duration_seconds,
    round(session_duration_seconds / 60, 2)     as session_duration_minutes,
    total_events,
    orders_in_session,
    payment_failures,
    order_drops,
    case
        when session_duration_seconds < 60      then 'Quick'
        when session_duration_seconds <=300     then 'Normal'
        else                                         'Long'
    end                                         as session_length_category
from session_events