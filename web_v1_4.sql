create table if not exists public.video_asset (
  id serial primary key,
  title varchar(220) not null default '',
  media_type varchar(20) not null default 'video',
  storage_path text default '',
  public_url text not null default '',
  mime_type varchar(120) default '',
  file_size bigint default 0,
  uploaded_by_user_id integer references public."user"(id) on delete set null,
  active boolean default true,
  created_at timestamp without time zone default now()
);
create table if not exists public.video_screen (
  id serial primary key,
  name varchar(180) not null,
  player_token varchar(180) not null unique,
  city varchar(120) default '',
  location_name varchar(220) default '',
  device_label varchar(180) default '',
  current_asset_id integer references public.video_asset(id) on delete set null,
  playlist_json text default '[]',
  rotation_degrees integer default 0,
  fit_mode varchar(20) default 'contain',
  loop_media boolean default true,
  muted boolean default true,
  enabled boolean default true,
  slide_duration_seconds integer default 10,
  last_seen_at timestamp without time zone,
  last_ip varchar(120) default '',
  created_at timestamp without time zone default now(),
  updated_at timestamp without time zone default now()
);
create table if not exists public.festive_session (
  id serial primary key,
  name varchar(180) not null default 'Festive Takeover',
  asset_id integer references public.video_asset(id) on delete set null,
  active boolean default false,
  started_by_user_id integer references public."user"(id) on delete set null,
  started_at timestamp without time zone default now(),
  ended_at timestamp without time zone,
  notes text default ''
);
create index if not exists idx_video_asset_active on public.video_asset(active);
create index if not exists idx_video_screen_city on public.video_screen(city);
create index if not exists idx_video_screen_enabled on public.video_screen(enabled);
create index if not exists idx_festive_session_active on public.festive_session(active);
alter table public.video_asset enable row level security;
alter table public.video_screen enable row level security;
alter table public.festive_session enable row level security;
insert into storage.buckets (id,name,public) values ('video-wall-media','video-wall-media',true) on conflict (id) do update set public=excluded.public;
