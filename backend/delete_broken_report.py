import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'advance_company.settings')
django.setup()

from apps.reports.models import Report

print("="*60)
print("Deleting Broken Report")
print("="*60)

# Find the specific broken report
broken_report = Report.objects.filter(id=10).first()

if broken_report:
    print(f"\nFound broken report:")
    print(f"  ID: {broken_report.id}")
    print(f"  Title: {broken_report.title}")
    print(f"  URL: {broken_report.file_url}")
    print(f"  Status: {broken_report.status}")
    
    broken_report.delete()
    print(f"\n✅ Deleted report ID 10")
else:
    print("\n✅ Report ID 10 already deleted or not found")

# Also delete any other reports with old URL pattern
other_broken = Report.objects.filter(
    file_url__contains='/documents/'
).exclude(file_url__contains='/reports/')

if other_broken.exists():
    count = other_broken.count()
    print(f"\nFound {count} other broken reports with old URL pattern")
    other_broken.delete()
    print(f"✅ Deleted {count} broken reports")

print("\n" + "="*60)
print("✅ Cleanup complete!")
print("All remaining reports should have working URLs.")
print("="*60)


