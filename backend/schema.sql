-- Run this in the Supabase SQL editor (or any Postgres) if you prefer to create tables by hand.
-- The API also creates these automatically on startup (SQLAlchemy create_all), so this is optional.

create table if not exists quotes (
  id serial primary key,
  name varchar(120) not null,
  phone varchar(32) not null,
  service varchar(32) not null,
  property_size varchar(16) not null,
  rooms integer not null,
  address varchar(255) not null,
  preferred_date date,
  frequency varchar(16) not null default 'once',
  est_low integer not null,
  est_high integer not null,
  status varchar(16) not null default 'new',
  owner_notified integer not null default 0,
  created_at timestamptz not null default now()
);
create index if not exists ix_quotes_phone on quotes(phone);

create table if not exists bookings (
  id serial primary key,
  name varchar(120),
  phone varchar(32) not null,
  service varchar(32) not null,
  scheduled_date date not null,
  address varchar(255) not null,
  frequency varchar(16) not null default 'once',
  status varchar(24) not null default 'pending',
  source varchar(16) not null default 'whatsapp',
  quote_id integer references quotes(id),
  parent_id integer references bookings(id),
  reminder_sent_at timestamptz,
  created_at timestamptz not null default now()
);
create index if not exists ix_bookings_phone on bookings(phone);
create index if not exists ix_bookings_date on bookings(scheduled_date);
create index if not exists ix_bookings_status on bookings(status);

create table if not exists conversations (
  phone varchar(32) primary key,
  state varchar(24) not null default 'idle',
  data jsonb not null default '{}'::jsonb,
  updated_at timestamptz not null default now()
);

create table if not exists message_log (
  id serial primary key,
  direction varchar(8) not null,
  phone varchar(32) not null,
  body text not null,
  mode varchar(8) not null default 'mock',
  created_at timestamptz not null default now()
);
create index if not exists ix_message_log_phone on message_log(phone);

-- The API connects with the database owner role, so enable RLS to block the public
-- Supabase REST/anon endpoints from reading these tables:
alter table quotes enable row level security;
alter table bookings enable row level security;
alter table conversations enable row level security;
alter table message_log enable row level security;
