-- Business Question: How are users segmented by behaviour, device and demographics?
-- Metrics: User counts, order rates by segment

with users as (
    select * from {{ ref('stg_users') }}
),

events as (
    select * from {{ ref('stg_events') }}
),

user_activity as (
    select
        user_id,
        count(distinct session_id)                          as total_sessions,
        countif(event_type = 'order_placed')                as total_orders,
        min(event_date)                                     as first_event_date,
        max(event_date)                                     as last_event_date
    from events
    group by user_id
),

final as (
    select
        u.user_id,
        u.city,
        u.device,
        u.age_group,
        u.signup_date,
        coalesce(a.total_sessions, 0)                       as total_sessions,
        coalesce(a.total_orders, 0)                         as total_orders,
        a.first_event_date,
        a.last_event_date,
        case
            when coalesce(a.total_orders, 0) = 0            then 'Never Ordered'
            when coalesce(a.total_orders, 0) between 1 and 3 then 'Low Value'
            when coalesce(a.total_orders, 0) between 4 and 10 then 'Mid Value'
            else 'High Value'
        end                                                 as user_segment
    from users u
    left join user_activity a on u.user_id = a.user_id
)

select * from final