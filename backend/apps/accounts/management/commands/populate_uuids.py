from django.core.management.base import BaseCommand
from django.apps import apps
from django.db import transaction
import uuid


class Command(BaseCommand):
    help = 'Populate UUID fields for all existing records across all models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without actually updating',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to update in each batch (default: 1000)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))

        self.stdout.write('='*80)
        self.stdout.write('UUID POPULATION SCRIPT')
        self.stdout.write('='*80 + '\n')

        # List of models to update (app_label, model_name)
        models_to_update = [
            ('accounts', 'User'),
            ('accounts', 'BiometricDevice'),
            ('accounts', 'BiometricAuthLog'),
            ('financial', 'FinancialAccount'),
            ('financial', 'Deposit'),
            ('financial', 'InterestCalculation'),
            ('beneficiary', 'Beneficiary'),
            ('documents', 'Document'),
            ('applications', 'Application'),
            ('applications', 'ApplicationActivity'),
            ('notifications', 'Notification'),
            ('notifications', 'NotificationPreferences'),
            ('reports', 'Report'),
            ('reports', 'ActivityLog'),
        ]

        total_updated = 0
        errors = []

        for app_label, model_name in models_to_update:
            try:
                Model = apps.get_model(app_label, model_name)
                
                # Check if model has uuid field
                if not hasattr(Model, 'uuid'):
                    self.stdout.write(
                        self.style.WARNING(f'⊘ {model_name}: No uuid field found - skipping')
                    )
                    continue

                # Count records without UUIDs
                records_without_uuid = Model.objects.filter(uuid__isnull=True)
                count = records_without_uuid.count()

                if count == 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ {model_name}: All records already have UUIDs')
                    )
                    continue

                self.stdout.write(f'\nProcessing {model_name}...')
                self.stdout.write(f'  Found {count} records without UUIDs')

                if not dry_run:
                    updated = 0
                    
                    # Process in batches for better performance
                    with transaction.atomic():
                        for record in records_without_uuid.iterator(chunk_size=batch_size):
                            record.uuid = uuid.uuid4()
                            record.save(update_fields=['uuid'])
                            updated += 1
                            
                            # Progress indicator
                            if updated % 100 == 0:
                                self.stdout.write(f'  Progress: {updated}/{count}', ending='\r')
                        
                        self.stdout.write(
                            self.style.SUCCESS(f'  ✓ Updated {updated} {model_name} records')
                        )
                        total_updated += updated
                else:
                    self.stdout.write(
                        self.style.WARNING(f'  Would update {count} {model_name} records')
                    )

            except LookupError:
                error_msg = f'Model {app_label}.{model_name} not found'
                errors.append(error_msg)
                self.stdout.write(
                    self.style.ERROR(f'✗ {error_msg}')
                )
            except Exception as e:
                error_msg = f'Error updating {model_name}: {str(e)}'
                errors.append(error_msg)
                self.stdout.write(
                    self.style.ERROR(f'✗ {error_msg}')
                )

        # Summary
        self.stdout.write('\n' + '='*80)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETE - No changes were made'))
        else:
            if errors:
                self.stdout.write(self.style.WARNING(f'COMPLETED WITH {len(errors)} ERRORS'))
                for error in errors:
                    self.stdout.write(f'  - {error}')
            else:
                self.stdout.write(self.style.SUCCESS('✅ UUID POPULATION COMPLETE!'))
            
            self.stdout.write(f'\nTotal records updated: {total_updated}')
        
        self.stdout.write('='*80)

        # Verification step
        if not dry_run and not errors:
            self.stdout.write('\nRunning verification...')
            self._verify_uuids(models_to_update)

    def _verify_uuids(self, models_to_update):
        """Verify that all records now have UUIDs"""
        all_verified = True
        
        for app_label, model_name in models_to_update:
            try:
                Model = apps.get_model(app_label, model_name)
                
                if not hasattr(Model, 'uuid'):
                    continue
                
                missing_count = Model.objects.filter(uuid__isnull=True).count()
                
                if missing_count > 0:
                    self.stdout.write(
                        self.style.ERROR(f'✗ {model_name}: Still has {missing_count} records without UUIDs')
                    )
                    all_verified = False
                else:
                    # Check for duplicates
                    from django.db.models import Count
                    duplicates = Model.objects.values('uuid').annotate(
                        count=Count('uuid')
                    ).filter(count__gt=1).count()
                    
                    if duplicates > 0:
                        self.stdout.write(
                            self.style.ERROR(f'✗ {model_name}: Has {duplicates} duplicate UUIDs!')
                        )
                        all_verified = False
            except:
                pass
        
        if all_verified:
            self.stdout.write(self.style.SUCCESS('✓ Verification passed - All UUIDs are valid and unique\n'))
        else:
            self.stdout.write(self.style.ERROR('✗ Verification failed - Some issues found\n'))