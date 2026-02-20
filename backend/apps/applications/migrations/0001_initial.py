from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        # Accounts must be migrated first so accounts_user table exists
        ('accounts', '__latest__'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                -- ============================================================
                -- Drop existing tables (cascade removes FK constraints too)
                -- ============================================================
                DROP TABLE IF EXISTS applications_applicationactivity CASCADE;
                DROP TABLE IF EXISTS applications_application CASCADE;

                -- ============================================================
                -- Recreate applications_application
                -- user_id and reviewed_by_id reference accounts_user.uuid
                -- ============================================================
                CREATE TABLE applications_application (
                    id              uuid            PRIMARY KEY,
                    application_type varchar(50)    NOT NULL,
                    reason          text            NOT NULL,
                    supporting_document varchar(100),
                    status          varchar(20)     NOT NULL DEFAULT 'pending',
                    admin_comments  text,
                    submitted_at    timestamptz     NOT NULL DEFAULT now(),
                    reviewed_at     timestamptz,
                    approved_at     timestamptz,
                    created_at      timestamptz     NOT NULL DEFAULT now(),
                    updated_at      timestamptz     NOT NULL DEFAULT now(),
                    user_id         uuid            NOT NULL
                        REFERENCES accounts_user(uuid) ON DELETE CASCADE,
                    reviewed_by_id  uuid
                        REFERENCES accounts_user(uuid) ON DELETE SET NULL
                );

                -- ============================================================
                -- Recreate applications_applicationactivity
                -- application_id references applications_application.id (uuid)
                -- user_id references accounts_user.uuid
                -- ============================================================
                CREATE TABLE applications_applicationactivity (
                    id              uuid            PRIMARY KEY,
                    action          varchar(50)     NOT NULL,
                    notes           text,
                    created_at      timestamptz     NOT NULL DEFAULT now(),
                    application_id  uuid            NOT NULL
                        REFERENCES applications_application(id) ON DELETE CASCADE,
                    user_id         uuid            NOT NULL
                        REFERENCES accounts_user(uuid) ON DELETE CASCADE
                );

                -- ============================================================
                -- Indexes
                -- ============================================================
                CREATE INDEX idx_application_user        ON applications_application(user_id);
                CREATE INDEX idx_application_status      ON applications_application(status);
                CREATE INDEX idx_application_type        ON applications_application(application_type);
                CREATE INDEX idx_application_created     ON applications_application(created_at DESC);
                CREATE INDEX idx_activity_application    ON applications_applicationactivity(application_id);
                CREATE INDEX idx_activity_user           ON applications_applicationactivity(user_id);
                CREATE INDEX idx_activity_created        ON applications_applicationactivity(created_at DESC);
            """,
            reverse_sql="""
                DROP TABLE IF EXISTS applications_applicationactivity CASCADE;
                DROP TABLE IF EXISTS applications_application CASCADE;
            """
        ),
    ]