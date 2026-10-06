-- Ndolè database schema for Supabase (PostgreSQL).
-- Reconstructed from the application models (model.py) and queries (utils/*.py).
-- Run it once in the Supabase SQL editor of a new project.
--
-- Access model: the Streamlit server is the only client. It talks to Supabase with the
-- key from .streamlit/secrets.toml, which never reaches the browser. Row Level Security
-- is enabled with no policies, so these tables are reachable only with the service_role
-- key: use that key in secrets.toml (and keep it secret), or write your own policies.

create table if not exists public.users (
    user_id                  text primary key,          -- = auth.users.id
    username                 text not null unique,
    profile_picture          text,
    created_at               text not null,             -- ISO 8601 timestamps (stored as text by the app)
    last_login               text,
    learning_preferences     jsonb not null default '{}'::jsonb,
    repositories             jsonb not null default '[]'::jsonb,   -- repo ids
    document_accessed        jsonb not null default '[]'::jsonb,   -- Access objects
    liked_documents          jsonb not null default '[]'::jsonb,
    disliked_documents       jsonb not null default '[]'::jsonb,
    bookmarked_documents     jsonb not null default '[]'::jsonb,
    shared_documents         jsonb not null default '[]'::jsonb,
    chat_histories           jsonb not null default '[]'::jsonb,   -- chat ids
    experience_points        integer not null default 0,
    badges                   jsonb not null default '[]'::jsonb,
    daily_challenges         jsonb not null default '{}'::jsonb,
    study_stats              jsonb not null default '[]'::jsonb,   -- one StudyStats per active day
    followers                jsonb not null default '[]'::jsonb,
    following                jsonb not null default '[]'::jsonb,
    is_deleted               boolean not null default false,
    telegram_id              text,
    notification_preferences jsonb not null default '{}'::jsonb
);

create table if not exists public.document_repositories (
    repo_id              text primary key,
    name                 text not null,
    description          text not null default '',
    is_public            boolean not null default false,
    is_deleted           boolean not null default false,
    owner_id             text not null references public.users(user_id),
    created_at           text not null,
    updated_at           text not null,
    categories           jsonb not null default '[]'::jsonb,
    documents            jsonb not null default '[]'::jsonb,   -- doc ids (a document can be in several repos)
    banner               text,                                  -- "banners/<path>" in Storage
    accesses             jsonb not null default '[]'::jsonb,
    likes                jsonb not null default '[]'::jsonb,
    dislikes             jsonb not null default '[]'::jsonb,
    bookmarks            jsonb not null default '[]'::jsonb,
    shares               jsonb not null default '[]'::jsonb,
    number_of_indexed    integer not null default 0,
    related_repositories jsonb not null default '[]'::jsonb
);
create index if not exists document_repositories_public_idx
    on public.document_repositories (is_public, is_deleted, updated_at desc);

create table if not exists public.documents (
    doc_id            text primary key,
    title             text not null,
    description       text not null default '',
    file_size         integer not null,
    file_path         text not null,                          -- "documents/<owner>/<doc>.pdf" in Storage
    upload_date       text not null,
    category          text,
    original_repo     text not null,
    type              text not null default 'simple_text',
    cover             text,                                   -- "covers/<path>" in Storage
    word_count        integer,
    page_count        integer,
    owner_id          text not null references public.users(user_id),
    is_deleted        boolean not null default false,
    related_documents jsonb not null default '[]'::jsonb
);

create table if not exists public.chunks (
    chunk_id    text primary key,
    document_id text not null references public.documents(doc_id),
    position    integer not null,
    page        integer not null,                             -- 0-based page number
    text        text not null,
    embedding   jsonb not null                                -- 384 floats (all-MiniLM-L6-v2)
);
create index if not exists chunks_document_idx on public.chunks (document_id);

create table if not exists public.chat_histories (
    chat_id      text primary key,
    owner_id     text not null references public.users(user_id),
    title        text not null default 'New Conversation',
    created_at   text not null,
    last_message jsonb,
    messages     jsonb not null default '[]'::jsonb,          -- message ids, in order
    repo_source  text not null,
    type         text not null,                               -- qa | course | exercise
    is_deleted   boolean not null default false,
    mode         boolean not null default false                -- course/exercise generated, follow-up Q&A active
);

create table if not exists public.messages (
    message_id   text primary key,
    chat_id      text not null references public.chat_histories(chat_id),
    received_at  text not null,
    content      text not null,
    is_assistant boolean not null default false,
    is_deleted   boolean not null default false,
    score        jsonb not null default '{}'::jsonb           -- quiz results
);
create index if not exists messages_chat_idx on public.messages (chat_id);

alter table public.users                 enable row level security;
alter table public.document_repositories enable row level security;
alter table public.documents             enable row level security;
alter table public.chunks                enable row level security;
alter table public.chat_histories        enable row level security;
alter table public.messages              enable row level security;

-- Private Storage buckets; files are served through short-lived signed URLs.
insert into storage.buckets (id, name, public)
values ('documents', 'documents', false), ('banners', 'banners', false), ('covers', 'covers', false)
on conflict (id) do nothing;
