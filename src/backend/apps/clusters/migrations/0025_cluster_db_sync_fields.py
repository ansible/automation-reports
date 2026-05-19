from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clusters', '0024_delete_costs'),
    ]

    operations = [
        migrations.AddField(
            model_name='cluster',
            name='sync_mode',
            field=models.CharField(
                choices=[('api', 'API (OAuth2)'), ('database', 'Direct Database')],
                default='api',
                max_length=20,
            ),
        ),
        migrations.AddField(
            model_name='cluster',
            name='db_host',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='cluster',
            name='db_port',
            field=models.IntegerField(default=5432),
        ),
        migrations.AddField(
            model_name='cluster',
            name='db_name',
            field=models.CharField(blank=True, default='awx', max_length=255),
        ),
        migrations.AddField(
            model_name='cluster',
            name='db_user',
            field=models.CharField(blank=True, default='', max_length=255),
        ),
        migrations.AddField(
            model_name='cluster',
            name='db_password',
            field=models.BinaryField(default=b''),
        ),
    ]
