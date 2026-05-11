# Deferred Work

## Deferred from: code review of 1-1-project-initialization-containerized-environment.md (2026-05-09)

- **Performance/Permission issues with Windows volume bind**: `volumes: - .:/app` on Windows can be slow or cause file lock issues in some Podman/Docker setups. This is a known environmental quirk for local development on Windows.

## Deferred from: code review of 1-3-multi-tenant-database-schema-sqlmodel.md (2026-05-09)

- **Lack of Alembic/Migrations**: `create_all` is used for dev but no migration strategy (Alembic) is introduced for production readiness.
