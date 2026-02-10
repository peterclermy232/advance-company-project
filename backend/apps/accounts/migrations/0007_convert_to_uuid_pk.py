from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0006_make_uuid_unique'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            DO $$ 
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT
                        tc.table_schema,
                        tc.table_name,
                        tc.constraint_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu 
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    JOIN information_schema.constraint_column_usage ccu 
                        ON ccu.constraint_name = tc.constraint_name
                        AND ccu.table_schema = tc.table_schema
                    WHERE tc.constraint_type = 'FOREIGN KEY'
                    AND ccu.table_name = 'accounts_user'
                    AND ccu.column_name = 'id'
                ) LOOP
                    EXECUTE format('ALTER TABLE %I.%I DROP CONSTRAINT IF EXISTS %I CASCADE', 
                                   r.table_schema, r.table_name, r.constraint_name);
                END LOOP;
            END $$;
            
            ALTER TABLE accounts_user DROP CONSTRAINT IF EXISTS accounts_user_pkey CASCADE;
            
            DO $$
            BEGIN
                ALTER TABLE accounts_user DROP CONSTRAINT IF EXISTS accounts_user_uuid_key CASCADE;
            EXCEPTION
                WHEN undefined_object THEN NULL;
            END $$;
            
            ALTER TABLE accounts_user ALTER COLUMN uuid SET NOT NULL;
            ALTER TABLE accounts_user ADD CONSTRAINT accounts_user_pkey PRIMARY KEY (uuid);
            ALTER TABLE accounts_user DROP COLUMN IF EXISTS id CASCADE;
            """,
            reverse_sql=migrations.RunSQL.noop
        ),
    ]
