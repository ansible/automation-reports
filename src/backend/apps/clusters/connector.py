import datetime
import logging
import os
from abc import ABC
from urllib.parse import urlsplit

import requests
from crontab import CronTab
from django.db import transaction

from backend.apps.clusters.models import (
    ClusterSyncData,
    ClusterSyncStatus,
    JobTemplate,
    Job,
    Organization
)
from backend.apps.clusters.schemas import ClusterSchema

logger = logging.getLogger("automation-reports")


class ApiConnector(ABC):

    def __init__(self,
                 cluster: ClusterSchema,
                 timeout=30,
                 since: datetime.datetime | None = None,
                 until: datetime.datetime | None = None,
                 managed: bool = False):

        self.cluster = cluster
        self.timeout = timeout
        self.managed = managed

        try:
            cluster_sync_data = ClusterSyncStatus.objects.get(cluster=self.cluster)
        except ClusterSyncStatus.DoesNotExist:
            cluster_sync_data = ClusterSyncStatus(cluster=self.cluster)
        self.cluster_sync_data = cluster_sync_data

        self.until = until

        if self.managed:
            self.since = since
        else:
            if since is not None:
                self.since = since
            elif self.cluster_sync_data.last_job_finished_date is not None and self.managed is False:
                self.since = self.cluster_sync_data.last_job_finished_date
            else:
                now = datetime.datetime.now(datetime.timezone.utc)
                cron_entry = os.environ.get("CRON_SYNC", "0 */1 * * *")
                entry = CronTab(cron_entry)
                self.since = entry.previous(now=now, default_utc=True, return_datetime=True)

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
        if self.until is not None:
            until = self.until.isoformat().replace('+00:00', 'Z')
            parameters += f'&finished__lte={until}'
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

    def sync_common(self, sync_type):
        if sync_type == 'organization':
            endpoint = f'/api/v2/organizations/?page_size=100&page=1'
            qs = Organization.objects.filter(cluster=self.cluster)

        elif sync_type == 'job_template':
            endpoint = f'/api/v2/job_templates/?page_size=200&page=1'
            qs = JobTemplate.objects.filter(cluster=self.cluster)
        else:
            raise NotImplementedError
        response = self.execute_get(endpoint)
        response_data = []
        db_organizations = {}
        if sync_type == 'job_template':
            db_organizations = {org.external_id: org for org in Organization.objects.filter(cluster=self.cluster)}
        db_data = {data.external_id: data for data in qs}

        for results in response:
            for result in results:
                db_item = db_data.pop(result["id"], None)

                if sync_type == 'job_template':
                    external_organization = result.get("summary_fields", {}).get("organization", {}).get("id", None)
                    if external_organization:
                        organization = db_organizations.get(external_organization, None)
                    else:
                        organization = None
                else:
                    organization = None

                if db_item is not None:
                    db_item.name = result["name"]
                    db_item.description = result["description"]
                    if sync_type == 'job_template':
                        db_item.organization = organization
                    db_item.save()
                else:
                    if sync_type == 'job_template':
                        JobTemplate.objects.create(
                            cluster=self.cluster,
                            name=result["name"],
                            description=result["description"],
                            external_id=result["id"],
                            organization=organization,
                        )
                    elif sync_type == 'organization':
                        Organization.objects.create(
                            cluster=self.cluster,
                            name=result["name"],
                            description=result["description"],
                            external_id=result["id"],
                        )
                response_data.append(result["id"])
        if sync_type == 'job_template':
            for key, value in db_data.items():
                logger.info(f"Deleting job template {value.name} with id {value.id}")
                count = Job.objects.filter(job_template_id=value.id, cluster_id=value.cluster_id).count()
                if count == 0:
                    value.delete()

    def sync(self):
        logger.info('Check status of cluster')
        time_out = self.timeout
        self.timeout = 3
        ping = self.ping
        if ping is None:
            logger.info(f'Cluster {self.base_url} is not reachable.')
            raise Exception(f'Cluster {self.base_url} is not reachable.')
        self.timeout = time_out

        self.sync_common('organization')
        self.sync_common('job_template')

        for job in self.jobs:
            logger.info("Checking status of job %s", job)
            job_id = job.get("id", None)
            finished = job.get("finished", None)
            if job_id is None or finished is None:
                logger.warning(f"Missing id or finished date time in job: {job}", )
                continue
            try:
                finished = datetime.datetime.fromisoformat(finished).astimezone(datetime.timezone.utc)
            except ValueError:
                raise TypeError(f"finished must be of type datetime.datetime job: {finished}")

            job["host_summaries"] = []

            logger.info(f"Job {job_id} retrieving host summaries.")

            for host_summary in self.job_host_summaries(job_id):
                job["host_summaries"].append(host_summary)

            with (transaction.atomic()):
                logger.info(f"Job {job_id} saving data.")
                self.cluster_sync_data.last_job_finished_date = finished if self.cluster_sync_data.last_job_finished_date is None or finished > self.cluster_sync_data.last_job_finished_date else self.cluster_sync_data.last_job_finished_date
                self.cluster_sync_data.save()
                ClusterSyncData.objects.create(cluster=self.cluster, data=job)
