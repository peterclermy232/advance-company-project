from django.core.management.base import BaseCommand
from apps.reports.models import Report
from cloudinary.utils import cloudinary_url
import time
import re


class Command(BaseCommand):
    help = 'Regenerate signed URLs for existing Cloudinary reports'

    def handle(self, *args, **options):
        # Get all reports with Cloudinary URLs
        reports = Report.objects.filter(
            file_url__icontains='cloudinary.com'
        ).exclude(status='PENDING')
        
        self.stdout.write(f"Found {reports.count()} reports to update")
        
        updated_count = 0
        failed_count = 0
        
        for report in reports:
            try:
                # Extract public_id from the existing URL
                # URL format: https://res.cloudinary.com/dd9ooasmq/raw/upload/v1770032011/reports/financial/financial_report_user1_20260202_143330.pdf
                match = re.search(r'/v\d+/(.+\.pdf)$', report.file_url)
                
                if not match:
                    self.stdout.write(self.style.WARNING(
                        f"Could not parse URL for report {report.id}: {report.file_url}"
                    ))
                    failed_count += 1
                    continue
                
                public_id = match.group(1)
                
                # Generate new signed URL
                signed_url, options = cloudinary_url(
                    public_id,
                    resource_type='raw',
                    type='upload',  # Try with original type first
                    sign_url=True,
                    secure=True,
                    expires_at=int(time.time()) + (30 * 24 * 60 * 60)  # 30 days
                )
                
                # Update report
                report.file_url = signed_url
                report.save(update_fields=['file_url'])
                
                updated_count += 1
                self.stdout.write(self.style.SUCCESS(
                    f"Updated report {report.id}: {report.title}"
                ))
                
            except Exception as e:
                failed_count += 1
                self.stdout.write(self.style.ERROR(
                    f"Failed to update report {report.id}: {str(e)}"
                ))
        
        self.stdout.write(self.style.SUCCESS(
            f"\nCompleted! Updated: {updated_count}, Failed: {failed_count}"
        ))