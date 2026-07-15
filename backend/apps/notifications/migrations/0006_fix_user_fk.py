import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_convert_to_uuid_pk'),
        ('notifications', '0005_make_uuid_unique'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[migrations.RunSQL(
            sql="""
            TRUNCATE TABLE notifications_notificationpreferences CASCADE;
            
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT constraint_name 
                    FROM information_schema.table_constraints 
                    WHERE table_name = 'notifications_notificationpreferences'
                ) LOOP
                    EXECUTE 'ALTER TABLE notifications_notificationpreferences DROP CONSTRAINT IF EXISTS ' 
                            || quote_ident(r.constraint_name) || ' CASCADE';
                END LOOP;
            END $$;
            
            ALTER TABLE notifications_notificationpreferences DROP COLUMN IF EXISTS id CASCADE;
            
            DO $$ 
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'notifications_notificationpreferences' 
                    AND column_name = 'uuid'
                ) THEN
                    ALTER TABLE notifications_notificationpreferences 
                    ADD COLUMN uuid uuid NOT NULL DEFAULT gen_random_uuid();
                ELSE
                    ALTER TABLE notifications_notificationpreferences ALTER COLUMN uuid SET NOT NULL;
                END IF;
            END $$;
            
            ALTER TABLE notifications_notificationpreferences ADD CONSTRAINT notifications_notificationpreferences_pkey PRIMARY KEY (uuid);
            ALTER TABLE notifications_notificationpreferences ALTER COLUMN user_id TYPE uuid USING NULL;
            ALTER TABLE notifications_notificationpreferences ALTER COLUMN user_id SET NOT NULL;
            
            ALTER TABLE notifications_notificationpreferences
            ADD CONSTRAINT notifications_notificationpreferences_user_id_fkey
            FOREIGN KEY (user_id) REFERENCES accounts_user(uuid) ON DELETE CASCADE DEFERRABLE INITIALLY DEFERRED;
            
            ALTER TABLE notifications_notificationpreferences
            ADD CONSTRAINT notifications_notificationpreferences_user_id_key UNIQUE (user_id);
            """,
                reverse_sql=migrations.RunSQL.noop,
            )],
            # The raw SQL above changes the real database directly (drops
            # NotificationPreferences.id, adds uuid as its pk, repoints
            # user_id at accounts_user.uuid), so mirror those changes in
            # Django's state here. Without this, 0007_remove_notification_id_
            # and_more.py — auto-generated against the stale old state —
            # tries to redo them for real and fails against any database
            # built from scratch (fresh test DBs, new local/CI setups).
            state_operations=[
                migrations.RemoveField(
                    model_name='notificationpreferences',
                    name='id',
                ),
                migrations.AddField(
                    model_name='notificationpreferences',
                    name='uuid',
                    field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
                ),
            ],
        ),
    ]
