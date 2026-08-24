-- Refresh only the obsolete built-in partner URLs. Custom URLs are preserved.
update public.food_integration
set portal_url='https://partner.swiggy.com/login', updated_at=now()
where lower(platform)='swiggy'
  and rtrim(portal_url,'/')='https://partner.swiggy.com/v2';

update public.food_integration
set portal_url='https://www.zomato.com/partners/onlineordering/orders/', updated_at=now()
where lower(platform)='zomato'
  and rtrim(portal_url,'/')='https://www.zomato.com/partners';
