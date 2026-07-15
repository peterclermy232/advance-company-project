from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0009_alter_user_identity_document_and_more'),
    ]

    # accounts_biometricdevice.user_id and accounts_biometricauthlog.user_id
    # (plus accounts_biometricauthlog.device_id) were created back when
    # accounts_user's pk was still a bigint 'id' (see migration 0002), and
    # were never converted when 0007_convert_to_uuid_pk.py switched User to a
    # uuid pk. Unlike notifications (0006_fix_user_fk.py), nobody ever fixed
    # these, so any query touching a user's biometric_devices/biometric_logs
    # crashes with "operator does not exist: bigint = uuid" — including in
    # production, e.g. login/profile's has_biometric check.
    operations = [
        migrations.RunSQL(
            sql="""
            -- Records tied to the pre-conversion integer ids are unrelatable
            -- to any real uuid now, so clear them rather than trying to
            -- preserve unrelatable data.
            TRUNCATE TABLE accounts_biometricauthlog CASCADE;
            TRUNCATE TABLE accounts_biometricdevice CASCADE;

            DO $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN (
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_name = 'accounts_biometricdevice'
                    AND constraint_type = 'FOREIGN KEY'
                ) LOOP
                    EXECUTE 'ALTER TABLE accounts_biometricdevice DROP CONSTRAINT IF EXISTS '
                            || quote_ident(r.constraint_name) || ' CASCADE';
                END LOOP;

                FOR r IN (
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_name = 'accounts_biometricauthlog'
                    AND constraint_type = 'FOREIGN KEY'
                ) LOOP
                    EXECUTE 'ALTER TABLE accounts_biometricauthlog DROP CONSTRAINT IF EXISTS '
                            || quote_ident(r.constraint_name) || ' CASCADE';
                END LOOP;
            END $$;

            ALTER TABLE accounts_biometricdevice ALTER COLUMN user_id TYPE uuid USING NULL;
            ALTER TABLE accounts_biometricdevice ALTER COLUMN user_id SET NOT NULL;
            ALTER TABLE accounts_biometricdevice
                ADD CONSTRAINT accounts_biometricdevice_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES accounts_user(uuid) ON DELETE CASCADE;

            ALTER TABLE accounts_biometricauthlog ALTER COLUMN user_id TYPE uuid USING NULL;
            ALTER TABLE accounts_biometricauthlog ALTER COLUMN user_id SET NOT NULL;
            ALTER TABLE accounts_biometricauthlog
                ADD CONSTRAINT accounts_biometricauthlog_user_id_fkey
                FOREIGN KEY (user_id) REFERENCES accounts_user(uuid) ON DELETE CASCADE;

            ALTER TABLE accounts_biometricauthlog ALTER COLUMN device_id TYPE uuid USING NULL;
            ALTER TABLE accounts_biometricauthlog
                ADD CONSTRAINT accounts_biometricauthlog_device_id_fkey
                FOREIGN KEY (device_id) REFERENCES accounts_biometricdevice(uuid) ON DELETE SET NULL;
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
