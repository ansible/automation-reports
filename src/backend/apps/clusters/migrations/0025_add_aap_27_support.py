# Generated migration for AAP 2.7 support

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("clusters", "0024_delete_costs"),
    ]

    operations = [
        migrations.AlterField(
            model_name="cluster",
            name="aap_version",
            field=models.CharField(
                choices=[
                    ("AAP 2.7", "AAP 2.7"),
                    ("AAP 2.6", "AAP 2.6"),
                    ("AAP 2.5", "AAP 2.5"),
                    ("AAP 2.4", "AAP 2.4"),
                ],
                default="AAP 2.4",
                max_length=15,
            ),
        ),
    ]
