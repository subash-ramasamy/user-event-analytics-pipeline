-- Business Question: How do users progress through the purchase funnel daily?
-- Metrics: Search → Click → Cart → Order conversion rates

with events as (
    select * from {{ ref('stg_events') }}
),

funnel as (
    select
        event_date,
        countif(event_type = 'user_searched')       as searched,
        countif(event_type = 'restaurant_clicked')  as restaurant_clicked,
        countif(event_type = 'cart_added')          as cart_added,
        countif(event_type = 'order_placed')        as order_placed,
        countif(event_type = 'order_dropped')       as order_dropped,
        countif(event_type = 'payment_failed')      as payment_failed
    from events
    group by event_date
)

select
    event_date,
    searched,
    restaurant_clicked,
    cart_added,
    order_placed,
    order_dropped,
    payment_failed,
    round(safe_divide(restaurant_clicked, searched), 4)   as search_to_click_rate,
    round(safe_divide(cart_added, restaurant_clicked), 4) as click_to_cart_rate,
    round(safe_divide(order_placed, cart_added), 4)       as cart_to_order_rate,
    round(safe_divide(order_placed, searched), 4)         as overall_conversion_rate
from funnel
order by event_date