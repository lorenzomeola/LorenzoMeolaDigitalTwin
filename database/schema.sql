create table if not exists public.twin_contact_requests (
    id bigint generated always as identity primary key,
    email text not null check (char_length(email) <= 254),
    name text check (name is null or char_length(name) <= 120),
    notes text check (notes is null or char_length(notes) <= 1000),
    consent_confirmed_at timestamptz not null,
    created_at timestamptz not null default now()
);

create table if not exists public.twin_rate_limits (
    visitor_hash text not null check (char_length(visitor_hash) = 64),
    window_seconds integer not null check (window_seconds in (60, 86400)),
    window_start bigint not null,
    request_count integer not null check (request_count > 0),
    expires_at timestamptz not null,
    primary key (visitor_hash, window_seconds, window_start)
);

create index if not exists twin_rate_limits_expiry_idx
    on public.twin_rate_limits (expires_at);