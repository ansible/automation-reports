from django.db import migrations, models


def fix_null_org_job_templates(apps, schema_editor):
    """Fix JobTemplate rows with organization=NULL.

    For each null-org template, use the organization from its associated
    jobs to set the correct organization. When jobs reference multiple
    orgs, split into per-org templates and reassign job FKs. If a
    correct-org template already exists (from connector sync), merge
    jobs into it.

    Corner cases:
    1. No null-org templates: no-op.
    2. Template with zero jobs: skipped (can't determine org).
    3. All jobs have org=NULL: skipped (no data to infer from).
    4. Jobs with mixed orgs + some org=NULL: org=NULL jobs stay on the
       original template, which is kept (not deleted).
    5. Single org: one new template created, jobs reassigned, original deleted.
    6. Multiple orgs: per-org templates created, jobs split, original deleted.
    7. Correct-org template already exists (connector synced it): jobs merged
       into existing template, no new template created.
    8. Multiple null-org templates with same name (NULL != NULL in unique
       constraints): each processed independently; second may merge into
       template created by the first.
    9. external_id collision: existing-template check covers both unique
       constraints (cluster, name, org) and (cluster, external_id, org).
    10. Idempotent: second run finds no null-org templates, no-op.
    """
    JobTemplate = apps.get_model('clusters', 'JobTemplate')
    Job = apps.get_model('clusters', 'Job')

    for tmpl in JobTemplate.objects.filter(organization__isnull=True):
        org_ids = list(
            Job.objects.filter(job_template=tmpl, organization__isnull=False)
            .values_list('organization_id', flat=True)
            .distinct()
        )

        if len(org_ids) == 0:
            continue

        for org_id in org_ids:
            # Check both unique constraints: (cluster, name, org) and (cluster, external_id, org)
            existing = JobTemplate.objects.filter(
                cluster=tmpl.cluster, organization_id=org_id,
            ).filter(
                models.Q(name=tmpl.name) | models.Q(external_id=tmpl.external_id)
            ).first()

            if existing:
                Job.objects.filter(
                    job_template=tmpl, organization_id=org_id,
                ).update(job_template=existing)
            else:
                new_tmpl = JobTemplate.objects.create(
                    cluster=tmpl.cluster,
                    external_id=tmpl.external_id,
                    name=tmpl.name,
                    description=tmpl.description,
                    organization_id=org_id,
                    time_taken_manually_execute_minutes=tmpl.time_taken_manually_execute_minutes,
                    time_taken_create_automation_minutes=tmpl.time_taken_create_automation_minutes,
                )
                Job.objects.filter(
                    job_template=tmpl, organization_id=org_id,
                ).update(job_template=new_tmpl)

        # Defensive: keep template if jobs with org=NULL still reference it.
        # In practice AAP always sets organization on jobs, so this
        # branch is unlikely to be reached.
        if not Job.objects.filter(job_template=tmpl).exists():
            tmpl.delete()


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clusters', '0026_alter_subscriptioncost_monthly_subscription_cost'),
    ]

    operations = [
        migrations.RunPython(fix_null_org_job_templates, reverse_noop),
    ]
