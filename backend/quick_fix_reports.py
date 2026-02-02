import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'advance_company.settings')
django.setup()

from apps.reports.models import Report

print("="*70)
print("QUICK FIX - Delete Old Inaccessible Reports")
print("="*70)

# Find all reports with the old broken URLs
broken_reports = Report.objects.filter(
    file_url__contains='res.cloudinary.com/dd9ooasmq/raw/upload/documents/'
)

print(f"\n📊 Found {broken_reports.count()} reports with broken URLs\n")

if broken_reports.count() == 0:
    print("✅ No broken reports found!")
    sys.exit(0)

print("These reports will be DELETED:")
for report in broken_reports:
    print(f"   [{report.id}] {report.title} - {report.user.full_name}")

print("\n⚠️  Users will need to regenerate these reports.")
print("The new reports will have public URLs that work correctly.")

response = input("\nProceed with deletion? (yes/no): ")

if response.lower() == 'yes':
    count = broken_reports.count()
    broken_reports.delete()
    print(f"\n✅ Deleted {count} broken reports!")
    print("\nNext steps:")
    print("1. Replace views.py with the fixed version")
    print("2. Users can regenerate reports via the API")
    print("3. New reports will have working URLs")
else:
    print("\n❌ Cancelled. No reports were deleted.")


