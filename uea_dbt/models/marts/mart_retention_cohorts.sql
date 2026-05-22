-- Business Question: How well do we retain users over time?
-- Metrics: Weekly cohort retention rates by signup week

with users as (
    select * from {{ ref('stg_users') }}
),

events as (
    select * from {{ ref('stg_events') }}
),

user_cohorts as (
    select
        user_id,
        date_trunc(signup_date, week)               as cohort_week
    from users
),

user_activity as (
    select
        user_id,
        date_trunc(event_date, week)                as activity_week
    from events
    group by user_id, activity_week
),

cohort_activity as (
    select
        c.cohort_week,
        date_diff(a.activity_week, c.cohort_week, week) as week_number,
        count(distinct a.user_id)                   as active_users
    from user_cohorts c
    join user_activity a on c.user_id = a.user_id
    group by c.cohort_week, week_number
),

cohort_size as (
    select
        cohort_week,
        count(distinct user_id)                     as total_users
    from user_cohorts
    group by cohort_week
)

select
    ca.cohort_week,
    ca.week_number,
    cs.total_users                                  as cohort_size,
    ca.active_users,
    round(safe_divide(ca.active_users, cs.total_users), 4) as retention_rate
from cohort_activity ca
join cohort_size cs on ca.cohort_week = cs.cohort_week
order by ca.cohort_week, ca.week_number