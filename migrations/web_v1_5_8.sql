-- Tesla OS 27 historical compatibility
-- Reusable landlord and tenant profiles are encrypted by the application
-- before their payload is written to this table.

create table if not exists agreement_party_profile (
  id serial primary key,
  profile_type varchar(20) not null,
  name varchar(180) not null,
  data_ciphertext text not null default '',
  created_by_user_id integer null references "user"(id) on delete set null,
  created_at timestamp without time zone default now(),
  updated_at timestamp without time zone default now(),
  constraint uq_agreement_party_profile_name unique (profile_type, name),
  constraint ck_agreement_party_profile_type check (profile_type in ('landlord','tenant'))
);

create index if not exists ix_agreement_party_profile_type
  on agreement_party_profile (profile_type);
