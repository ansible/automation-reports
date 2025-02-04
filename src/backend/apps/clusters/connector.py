import datetime
from abc import ABC
from datetime import timedelta
from django.db import transaction

from backend.apps.clusters.models import ClusterSyncData, ClusterSyncStatus
from backend.apps.clusters.schemas import ClusterSchema
import requests
import logging
from urllib.parse import urlsplit
from backend_workers.workers import process_job_data

logger = logging.getLogger("automation-reports")


class ApiConnector(ABC):

    def __init__(self, cluster: ClusterSchema, timeout=30, since=None):
        self.cluster = cluster
        self.timeout = timeout
        try:
            cluster_sync_data = ClusterSyncStatus.objects.get(cluster=self.cluster)
        except ClusterSyncStatus.DoesNotExist:
            cluster_sync_data = ClusterSyncStatus(cluster=self.cluster)
        self.cluster_sync_data = cluster_sync_data

        if since is not None:
            self.since = since
        elif self.cluster_sync_data.last_job_finished_date is not None:
            self.since = self.cluster_sync_data.last_job_finished_date
        else:
            self.since = (datetime.datetime.now() - timedelta(hours=4)).astimezone(datetime.timezone.utc)

    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self.cluster.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    @property
    def base_url(self):
        return f'{self.cluster.protocol}://{self.cluster.address}:{self.cluster.port}'

    @property
    def ping(self):
        endpoint = '/api/v2/ping/'
        url = f'{self.base_url}{endpoint}'
        try:
            response = requests.get(
                url=url,
                verify=self.cluster.verify_ssl,
                timeout=self.timeout,
                headers=self.headers)
        except requests.exceptions.RequestException as e:
            return None
        if response.status_code != 200:
            return None
        return response.json()

    def execute_get(self, endpoint):
        _next = endpoint

        while _next is not None:
            url = f'{self.base_url}{_next}'
            logger.info(f'Executing GET request to {url}')
            try:
                response = requests.get(
                    url=url,
                    verify=self.cluster.verify_ssl,
                    timeout=self.timeout,
                    headers=self.headers)
            except requests.exceptions.RequestException as e:
                logger.error(f'GET request failed with exception {e}')
                break
            if response.status_code != 200:
                logger.error(f'GET request failed with status {response.status_code}')
                break
            response = response.json()
            next_page = response.get('next', None)
            results = response.get('results', response)
            if next_page:
                url_split = urlsplit(next_page)
                _next = f'{url_split.path}?{url_split.query}'
            else:
                _next = None
            yield results

    @property
    def jobs(self):
        parameters = ""
        if self.since is not None:
            since = self.since.isoformat().replace('+00:00', 'Z')
            parameters += f'&finished__gt={since}'
        endpoint = f'/api/v2/jobs/?page_size=100&page=1&order_by=finished{parameters}'
        response = self.execute_get(endpoint)
        for results in response:
            for result in results:
                yield result

    def job_host_summaries(self, job_id):
        endpoint = f'/api/v2/jobs/{job_id}/job_host_summaries?page_size=100&page=1&order_by=modified'
        response = self.execute_get(endpoint)
        for results in response:
            for result in results:
                yield result

    def sync(self):
        logger.info('Check status of cluster')
        time_out = self.timeout
        self.timeout = 3
        ping = self.ping
        if ping is None:
            logger.info(f'Cluster {self.base_url} is not reachable.')
            return
        self.timeout = time_out
        for job in self.jobs:
            job_id = job.get("id", None)
            finished = job.get("finished", None)

            if job_id is None or finished is None:
                continue
            try:
                finished = datetime.datetime.fromisoformat(finished).astimezone(datetime.timezone.utc)
            except ValueError:
                raise TypeError(f"finished must be of type datetime.datetime")
            job["host_summaries"] = []

            for host_summary in self.job_host_summaries(job_id):
                job["host_summaries"].append(host_summary)

            with transaction.atomic():
                self.cluster_sync_data.last_job_finished_date = finished
                self.cluster_sync_data.save()
                cluster_sync_data = ClusterSyncData.objects.create(cluster=self.cluster, data=job)

            process_job_data.send_with_options(args=(cluster_sync_data.id,))
