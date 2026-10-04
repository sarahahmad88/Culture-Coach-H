-- Run in your Supabase SQL editor. Use anon/publishable key, NEVER service-role.
create table public.training_attempts (
 id uuid primary key,
 user_id uuid not null references auth.users(id) on delete cascade,
 created_at timestamptz not null default now(),
 metadata jsonb not null,
 payload jsonb
);
alter table public.training_attempts enable row level security;
create policy "own select" on public.training_attempts for select to authenticated using ((select auth.uid()) = user_id);
create policy "own insert" on public.training_attempts for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "own update" on public.training_attempts for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
create policy "own delete" on public.training_attempts for delete to authenticated using ((select auth.uid()) = user_id);
revoke all on public.training_attempts from anon;
grant select, insert, update, delete on public.training_attempts to authenticated;
