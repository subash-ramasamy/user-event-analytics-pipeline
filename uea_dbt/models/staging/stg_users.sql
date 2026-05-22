with source as (
    select * from {{ source('uea_raw', 'users') }}
)

select
    user_id,
    coalesce(city, 'Unknown') as city,
    coalesce(device, 'Unknown') as device,
    signup_date,
    coalesce(age_group, 'Unknown') as age_group
from source
where user_id is not null