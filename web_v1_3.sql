-- Livenza Back Office Web 1.3 schema additions
alter table public."user" add column if not exists photo_data_uri text default '';
alter table public."user" add column if not exists aadhaar_last4 varchar(4) default '';
alter table public."user" add column if not exists aadhaar_name varchar(180) default '';
alter table public."user" add column if not exists aadhaar_verification_status varchar(40) default 'Not verified';
alter table public."user" add column if not exists aadhaar_verification_method varchar(80) default '';
alter table public."user" add column if not exists aadhaar_verification_ref varchar(180) default '';
alter table public."user" add column if not exists aadhaar_verified_at timestamp without time zone;
create table if not exists public.query_lead (id serial primary key,source varchar(60) default 'Manual',external_id varchar(180) default '',city varchar(120) default '',property_name varchar(180) default '',customer_name varchar(180) default '',mobile varchar(40) default '',whatsapp varchar(40) default '',email varchar(180) default '',query_text text default '',budget varchar(80) default '',move_in_date varchar(40) default '',stay_type varchar(80) default '',status varchar(40) default 'Live',heat varchar(20) default 'Warm',score integer default 50,assigned_user_id integer references public."user"(id),next_follow_up varchar(60) default '',notes text default '',raw_json text default '{}',created_at timestamp without time zone default now(),updated_at timestamp without time zone default now());
create table if not exists public.query_template (id serial primary key,name varchar(160) not null,category varchar(60) default 'General',message text default '',whatsapp_template_name varchar(160) default '',sources_json text default '[]',statuses_json text default '[]',auto_send boolean default false,active boolean default true,created_at timestamp without time zone default now());
create table if not exists public.query_activity (id serial primary key,query_id integer not null references public.query_lead(id) on delete cascade,action varchar(80) default 'Update',details text default '',actor_user_id integer references public."user"(id),created_at timestamp without time zone default now());
alter table public.query_lead enable row level security;
alter table public.query_template enable row level security;
alter table public.query_activity enable row level security;
