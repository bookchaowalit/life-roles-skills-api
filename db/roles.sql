-- Roles for the roles-skills database. Locally a superuser runs this; on Neon
-- `roles-skills-db provision` creates the same roles through the migrator.
--
-- roles_skills_migrator  owns the schema and runs migrations only.
-- roles_skills_api       the API at runtime: no superuser, no BYPASSRLS, owns nothing.
-- roles_skills_publisher sweeps and marks the outbox across workspaces; nothing else.

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'roles_skills_migrator') THEN
        CREATE ROLE roles_skills_migrator LOGIN NOSUPERUSER NOCREATEROLE NOBYPASSRLS;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'roles_skills_api') THEN
        CREATE ROLE roles_skills_api LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'roles_skills_publisher') THEN
        CREATE ROLE roles_skills_publisher LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOBYPASSRLS NOINHERIT;
    END IF;
END
$$;
