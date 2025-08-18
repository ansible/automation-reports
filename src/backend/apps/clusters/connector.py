import datetime
import logging
from urllib.parse import urlsplit

import requests
from django.db import transaction

from backend.apps.clusters.encryption import decrypt_value
from backend.apps.clusters.models import (
    ClusterSyncData,
    ClusterSyncStatus,
    JobTemplate,
    Job,
    Organization, ClusterVersionChoices
)
from backend.apps.clusters.schemas import ClusterSchema

logger = logging.getLogger("automation-reports")


class ApiConnector:

    def __init__(self,
                 cluster: ClusterSchema,
                 timeout=30,
                 since: datetime.datetime | None = None,
                 until: datetime.datetime | None = None,
                 managed: bool = False):

        self.cluster = cluster
        self.timeout = timeout
        self.managed = managed

        self.access_token = decrypt_value(cluster.access_token)

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
                '''
                Due to the possibility of a lot of data, we enable sync for the first sync only for the last day.
                '''
                yesterday = datetime.datetime.combine(
                    datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1),
                    datetime.datetime.min.time(),
                    tzinfo=datetime.timezone.utc)

                self.since = yesterday

    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def execute_get_one(self, url, timeout=None):
        logger.info(f'Executing GET request to {url}')
        try:
            response = requests.get(
                url=url,
                verify=self.cluster.verify_ssl,
                timeout=timeout if timeout is not None else self.timeout,
                headers=self.headers)
        except requests.exceptions.RequestException as e:
            logger.error(f'GET request failed with exception {e}')
            return None
        if response.status_code != 200:
            logger.error(f'GET request failed with status {response.status_code}')
            return None
        product_name = response.headers.get("X-Api-Product-Name", None)
        if product_name is None or product_name == "AWX":
            raise Exception("Not supported product.")
        response = response.json()
        return response

    def execute_get(self, endpoint):
        _next = endpoint
        results = []
        while _next is not None:
            url = f'{self.cluster.base_url}{_next}'
            response = self.execute_get_one(url)
            if response:
                next_page = response.get('next', None)
                results = response.get('results', response)
            else:
                next_page = None
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
        endpoint = f'{self.cluster.api_url}/jobs/?page_size=100&page=1&order_by=finished{parameters}'
        response = self.execute_get(endpoint)
        for results in response:
            for result in results:
                yield result

    def job_host_summaries(self, job_id):
        endpoint = f'{self.cluster.api_url}/jobs/{job_id}/job_host_summaries?page_size=100&page=1&order_by=modified'
        response = self.execute_get(endpoint)
        for results in response:
            for result in results:
                yield result

    def sync_common(self, sync_type):
        if sync_type == 'organization':
            endpoint = f'{self.cluster.api_url}/organizations/?page_size=100&page=1'
            qs = Organization.objects.filter(cluster=self.cluster)

        elif sync_type == 'job_template':
            endpoint = f'{self.cluster.api_url}/job_templates/?page_size=200&page=1'
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

    def ping(self, ping_url):
        logger.info(f'Pinging api {self.cluster.base_url}{ping_url}')
        url = f'{self.cluster.base_url}{ping_url}'
        return self.execute_get_one(url=url, timeout=5)

    @property
    def is_aap25_instance(self):
        logger.info(f'Checking if is AAP 2.5 at {self.cluster.base_url}')
        response = self.ping("/api/gateway/v1/ping/")
        return True if response is not None else False

    @property
    def is_aap24_instance(self):
        logger.info(f'Checking if is AAP 2.4 at {self.cluster.base_url}')
        response = self.ping("/api/v2/ping/")
        return True if response is not None else False

    def check_aap_version(self):
        logger.info(f'Checking AAP version at {self.cluster.base_url}')
        is_aap25_instance = self.is_aap25_instance
        if is_aap25_instance:
            if self.cluster.aap_version != ClusterVersionChoices.AAP25:
                self.cluster.aap_version = ClusterVersionChoices.AAP25
                self.cluster.save()
            return True

        is_aap24_instance = self.is_aap24_instance
        if is_aap24_instance:
            if self.cluster.aap_version != ClusterVersionChoices.AAP24:
                self.cluster.aap_version = ClusterVersionChoices.AAP24
                self.cluster.save()
            return True
        raise Exception(f'Not valid version for cluster {self.cluster.base_url}.')

    def sync_jobs(self):
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
