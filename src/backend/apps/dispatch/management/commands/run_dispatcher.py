import logging
import os
import redis
import yaml
from dispatcherd import run_service
from dispatcherd.config import setup as dispatcher_setup
from dispatcherd.factories import get_control_from_settings
from django.conf import settings
from django.core.management import BaseCommand, CommandError

from backend.analytics.subsystem_metrics import DispatcherMetricsServer
from backend.apps.dispatch.config import get_dispatcherd_config

logger = logging.getLogger('automation_dashboard.dispatch')


class Command(BaseCommand):
    help = 'Launch the task dispatcher'

    def add_arguments(self, parser):
        parser.add_argument('--status', dest='status', action='store_true', help='print the internal state of any running dispatchers')
        parser.add_argument('--schedule', dest='schedule', action='store_true', help='print the current status of schedules being ran by dispatcher')
        parser.add_argument('--running', dest='running', action='store_true', help='print the UUIDs of any tasked managed by this dispatcher')
        parser.add_argument(
            '--reload',
            dest='reload',
            action='store_true',
            help='cause the dispatcher to recycle all of its worker processes; running jobs will run to completion first',
        )
        parser.add_argument(
            '--cancel',
            dest='cancel',
            help=(
                'Cancel a particular task id. Takes either a single id string, or a JSON list of multiple ids. '
                'Can take in output from the --running argument as input to cancel all tasks. '
                'Only running tasks can be canceled, queued tasks must be started before they can be canceled.'
            ),
        )

    def verify_dispatcherd_socket(self):
        if not os.path.exists(settings.DISPATCHERD_DEBUGGING_SOCKFILE):
            raise CommandError('Dispatcher is not running locally')

    def handle(self, *arg, **options):
        config = get_dispatcherd_config()
        dispatcher_setup(config=config)
        if options.get('status'):
            ctl = get_control_from_settings()
            running_data = ctl.control_with_reply('status')
            if len(running_data) != 1:
                raise CommandError('Did not receive expected number of replies')
            return
        if options.get('schedule'):
            raise NotImplementedError()
        if options.get('running'):
            ctl = get_control_from_settings()
            running_data = ctl.control_with_reply('running')
            logger.debug('Running tasks: %s', running_data)
            return
        if options.get('reload'):
            raise NotImplementedError()
        if options.get('cancel'):
            cancel_str = options.get('cancel')
            try:
                cancel_data = yaml.safe_load(cancel_str)
            except Exception:
                cancel_data = [cancel_str]
            if not isinstance(cancel_data, list):
                cancel_data = [cancel_str]
            ctl = get_control_from_settings()
            results = []
            for task_id in cancel_data:
                # For each task UUID, send an individual cancel command
                result = ctl.control_with_reply('cancel', data={'uuid': task_id})
                results.append(result)
            logger.debug('Tasks: %s', results)
            return
        try:
            DispatcherMetricsServer().start()
        except redis.exceptions.ConnectionError as exc:
            raise CommandError(f'Dispatcher could not connect to redis, error: {exc}')

        run_service()
