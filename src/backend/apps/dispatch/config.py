from django.conf import settings

from backend.apps.dispatch.pool import get_auto_max_workers
from ansible_base.lib.utils.db import get_pg_notify_params


def get_dispatcherd_config(for_service: bool = False):
    config = {
        "version": 2,
        "service": {
            "pool_kwargs": {
                "min_workers": settings.JOB_EVENT_WORKERS,
                "max_workers": get_auto_max_workers(),
            },
            "main_kwargs": {
                "node_id": settings.CLUSTER_HOST_ID
            },
            "metrics_kwargs": {
                "log_level": "debug"
            },
            "process_manager_kwargs": {
                "preload_modules": [
                    "backend.apps.dispatch.hazmat"
                ]
            }
        },
        "worker": {
            "worker_kwargs": {
                "idle_timeout": 3
            }
        },
        "brokers": {
            "pg_notify": {
                "config": get_pg_notify_params(),
                "sync_connection_factory": "ansible_base.lib.utils.db.psycopg_connection_from_django",
                "channels": [
                    settings.DISPATCHER_SYNC_CHANNEL,
                    settings.DISPATCHER_PARSE_CHANNEL,
                ],
                "default_publish_channel": settings.CLUSTER_HOST_ID,
                "max_connection_idle_seconds": 5,
                "max_self_check_message_age_seconds": 2
            },
            "socket": {
                "socket_path": settings.DISPATCHERD_DEBUGGING_SOCKFILE
            }
        },
        "producers": {
            "ScheduledProducer": {
                "task_schedule": {
                    "lambda: __import__(\"time\").sleep(1)": {
                        "schedule": 3
                    },
                    "lambda: __import__(\"time\").sleep(2)": {
                        "schedule": 3
                    }
                }
            },
            "OnStartProducer": {
                "task_list": {
                    "lambda: print(\"This task runs on startup\")": {}
                }
            },
            "ControlProducer": None
        },
        "publish": {
            "default_control_broker": "socket",
            "default_broker": "pg_notify"
        }
    }

    if for_service:
        config["producers"] = {
            "ScheduledProducer": {"task_schedule": settings.DISPATCHER_SCHEDULE},
            "OnStartProducer": {"task_list": {"backend.apps.dispatch.tasks.dispatch_startup": {}}},
            "ControlProducer": {}
        }

    return config
