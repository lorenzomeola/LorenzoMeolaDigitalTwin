create table if not exists public.twin_contact_requests (
    id bigint generated always as identity primary key,
    email text not null check (char_length(email) <= 254),
    name text check (name is null or char_length(name) <= 120),
    notes text check (notes is null or char_length(notes) <= 1000),
    consent_confirmed_at timestamptz not null default now(),
    created_at timestamptz not null default now()
);

alter table public.twin_contact_requests enable row level security;

revoke all on table public.twin_contact_requests from anon, authenticated;
grant insert on table public.twin_contact_requests to service_role;