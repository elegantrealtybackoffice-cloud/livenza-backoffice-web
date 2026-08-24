alter table public."user" add column if not exists full_name varchar(180) default '';
alter table public."user" add column if not exists permissions_json text default '[]';
alter table public."user" add column if not exists active boolean default true;

create table if not exists public.city (
  id serial primary key,
  name varchar(120) unique not null,
  code varchar(30) default '',
  active boolean default true,
  created_at timestamp without time zone default now()
);
alter table public.city enable row level security;

alter table public.room add column if not exists city varchar(120) default '';
alter table public.tenant add column if not exists city varchar(120) default '';
update public."user" set active=true where active is null;
update public."user" set permissions_json='[]' where permissions_json is null;
create index if not exists idx_room_city on public.room(city);
create index if not exists idx_tenant_city on public.tenant(city);
