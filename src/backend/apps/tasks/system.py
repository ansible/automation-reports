import logging

from ansible_base.lib.utils.db import advisory_lock
from django.utils.timezone import now
from django.utils.translation import gettext_noop

from backend.apps.clusters.models import JobStatusChoices
from backend.apps.scheduler.models import SyncScheduleState, SyncSchedule, SyncJob, JobTypeChoices
from django.conf import settings

logger = logging.getLogger('automation_dashboard.tasks.system')


def automation_dashboard_periodic_scheduler():
    lock_session_timeout_milliseconds = settings.TASK_MANAGER_LOCK_TIMEOUT * 1000
    with advisory_lock('automation_dashboard_periodic_scheduler_lock', lock_session_timeout_milliseconds=lock_session_timeout_milliseconds, wait=False) as acquired:
        if acquired is False:
            logger.debug("Not running periodic scheduler, another task holds lock")
            return
        logger.debug("Starting periodic scheduler")

        run_now = now()
        state = SyncScheduleState.get_solo()
        last_run = state.schedule_last_run
        logger.debug("Last scheduler run was: %s", last_run)
        state.schedule_last_run = run_now
        state.save()

        old_schedules = SyncSchedule.objects.enabled().before(last_run)
        for schedule in old_schedules:
            schedule.update_computed_fields()

        schedules = SyncSchedule.objects.enabled().between(last_run, run_now)

        for schedule in schedules:
            cluster = schedule.cluster
            schedule.update_computed_fields()  # To update next_run timestamp.
            if cluster.cache_timeout_blocked:
                logger.warning("Cache timeout is in the future, bypassing schedule for cluster %s" % str(cluster.id))
                continue
            try:
                sync_kwargs = schedule.get_job_kwargs()
                new_job = schedule.cluster.create_sync_job(**sync_kwargs)
                logger.debug('Spawned {} from schedule {}-{}.'.format(new_job.log_format, schedule.name, schedule.pk))
                can_start = new_job.signal_start()
            except Exception:
                logger.exception("Failed to spawn new job")
                continue
            if not can_start:
                new_job.status = JobStatusChoices.FAILED
                new_job.job_explanation = gettext_noop(
                    "Scheduled job could not start because it \
                    was not in the right state"
                )
                new_job.save()


def automation_dashboard_job_parser_data_scheduler():
    lock_session_timeout_milliseconds = settings.TASK_MANAGER_LOCK_TIMEOUT * 1000
    with advisory_lock('automation_dashboard_job_parser_data_scheduler_lock', lock_session_timeout_milliseconds=lock_session_timeout_milliseconds, wait=False) as acquired:
        if acquired is False:
            logger.debug("Not running job data scheduler, another task holds lock")
            return
        logger.debug("Starting job data scheduler")
        max_jobs = settings.SCHEDULE_MAX_DATA_PARSE_JOBS
        job_data_schedules = SyncJob.objects.filter(type=JobTypeChoices.PARSE_JOB_DATA, status=JobStatusChoices.NEW)[:max_jobs]

        for job in job_data_schedules:
            job_data = job.cluster_sync_data
            if job_data is None:
                logger.warning("Job {} has no data".format(job.pk))
                continue

            if job_data.cache_timeout_blocked:
                logger.warning("Cache timeout is in the future, bypassing job parser for job %s" % str(job_data.id))
                continue
            try:
                can_start = job.signal_start()
            except Exception:
                logger.exception("Failed to spawn new data parser job")
                continue

            if not can_start:
                job.status = JobStatusChoices.FAILED
                job.job_explanation = gettext_noop(
                    "Data parse job could not start because it \
                    was not in the right state"
                )
                job.save()
