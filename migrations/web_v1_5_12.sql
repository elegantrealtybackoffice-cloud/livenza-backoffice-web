-- Tesla OS 27 historical compatibility
-- Personal live-avatar identity for the existing user profile.

alter table public."user" add column if not exists avatar_data_uri text default '';
alter table public."user" add column if not exists avatar_generation_mode varchar(40) default '';
alter table public."user" add column if not exists avatar_updated_at timestamp null;
