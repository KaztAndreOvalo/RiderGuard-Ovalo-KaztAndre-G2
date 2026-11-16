from django.db import migrations

PLATFORMS = [
    ("MAXIM", "Maxim"),
    ("MOVEIT", "MoveIt"),
    ("GRAB", "Grab"),
    ("LALAMOVE", "Lalamove"),
    ("FOODPANDA", "Foodpanda"),
    ("OTHER", "Other"),
]


def seed_platforms(apps, schema_editor):
    Platform = apps.get_model("trips", "Platform")
    for code, name in PLATFORMS:
        Platform.objects.get_or_create(code=code, defaults={"name": name})


def remove_platforms(apps, schema_editor):
    Platform = apps.get_model("trips", "Platform")
    Platform.objects.filter(code__in=[c for c, _ in PLATFORMS], trips__isnull=True).delete()


class Migration(migrations.Migration):
    dependencies = [("trips", "0001_initial")]
    operations = [migrations.RunPython(seed_platforms, remove_platforms)]
