create table if not exists public.food_integration (
  id serial primary key,
  platform varchar(60) not null default 'Other',
  display_name varchar(160) default '',
  outlet_id varchar(180) default '',
  account_identifier varchar(180) default '',
  portal_url text default '',
  developer_url text default '',
  api_base_url text default '',
  api_token_env varchar(120) default '',
  api_key_env varchar(120) default '',
  webhook_enabled boolean default true,
  api_enabled boolean default false,
  active boolean default true,
  last_sync_at timestamp without time zone,
  last_sync_status text default '',
  last_sync_count integer default 0,
  created_at timestamp without time zone default now(),
  updated_at timestamp without time zone default now()
);
create index if not exists idx_food_integration_platform on public.food_integration(platform);
create index if not exists idx_food_integration_active on public.food_integration(active);
alter table public.food_integration enable row level security;
insert into public.food_integration(platform,display_name,portal_url,developer_url,webhook_enabled,active)
select 'Swiggy','Swiggy Restaurant Partner','https://partner.swiggy.com/v2/','https://developers.swiggy.com/login',true,true
where not exists (select 1 from public.food_integration where lower(platform)='swiggy');
insert into public.food_integration(platform,display_name,portal_url,developer_url,webhook_enabled,active)
select 'Zomato','Zomato Restaurant Partner','https://www.zomato.com/partners','https://www.zomato.com/business/merchant-app',true,true
where not exists (select 1 from public.food_integration where lower(platform)='zomato');
insert into public.food_integration(platform,display_name,portal_url,developer_url,webhook_enabled,active)
select 'Toing','Toing Restaurant Partner','https://www.toingit.com/','',true,true
where not exists (select 1 from public.food_integration where lower(platform)='toing');
