import datetime
import logging
from urllib.parse import urlsplit

import pytz
from django.conf import settings
import requests
from django.db import transaction
import urllib3
import json

from backend.apps.clusters.encryption import decrypt_value, encrypt_value
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

        # Optionally suppress urllib3 SSL warnings
        if not settings.SHOW_URLLIB3_INSECURE_REQUEST_WARNING:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

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
                Due to the possibility of a lot of data,
                we enable sync for the initial sync configured in settings.
                '''
                initial_sync_days = getattr(settings, "INITIAL_SYNC_DAYS", 1)
                initial_sync_since = getattr(settings, "INITIAL_SYNC_SINCE", None)

                _date = None

                if initial_sync_since is not None:
                    try:
                        _date = datetime.datetime.fromisoformat(initial_sync_since)
                    except ValueError:
                        _date = None

                if _date is None:
                    _date = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=initial_sync_days)

                self.since = datetime.datetime.combine(_date.astimezone(pytz.UTC), datetime.datetime.min.time()).astimezone(pytz.UTC)

    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _reauth(self, timeout=None):
        url = f'{self.cluster.base_url}{self.cluster.oauth_token_url}'
        refresh_token = decrypt_value(self.cluster.refresh_token)
        client_id = self.cluster.client_id
        client_secret = decrypt_value(self.cluster.client_secret)

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        }
        auth = requests.auth.HTTPBasicAuth(client_id, client_secret)
        try:
            response = requests.post(
                url=url,
                data=data,
                auth=auth,
                verify=self.cluster.verify_ssl,
                timeout=timeout if timeout is not None else self.timeout,
                headers=headers)
        except requests.exceptions.RequestException as e:
            logger.error(f'Token refresh POST request failed with exception {e}')
            return False
        if not response.ok:
            logger.error(f'Token refresh POST request failed with status {response.status_code} url={url}, text={json.dumps(response.text)}')
            return False
        logger.info(f'Token refresh POST request succeeded with status {response.status_code}')
        resp = response.json()

        self.cluster.access_token = encrypt_value(resp['access_token'])
        self.cluster.refresh_token = encrypt_value(resp["refresh_token"])
        self.access_token = resp['access_token']
        self.cluster.save()

        return True

    def _get_with_reauth(self, url, timeout=None):
        # try 1st time
        try:
            response = requests.get(
                url=url,
                verify=self.cluster.verify_ssl,
                timeout=timeout if timeout is not None else self.timeout,
                headers=self.headers)
        except requests.exceptions.RequestException as e:
            logger.error(f'GET request failed with exception {e}')
            return None
        if response.ok:
            return response

        # Try to re-auth only after 401 error
        logger.error(f'GET request failed with status {response.status_code}')
        if response.status_code != 401:
            return response
        self._reauth()

        # try 2nd time
        try:
            response = requests.get(
                url=url,
                verify=self.cluster.verify_ssl,
                timeout=timeout if timeout is not None else self.timeout,
                headers=self.headers)
        except requests.exceptions.RequestException as e:
            logger.error( f'GET request failed with exception {e}')
            return None
        logger.error(f'GET after reauth response.status_code={response.status_code}')
        return  response

    def execute_get_one(self, url, timeout=None):
        logger.info(f'Executing GET request to {url}')
        response = self._get_with_reauth(url, timeout=timeout)
        if response is None or not response.ok:
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
        # Do same as execute_get_one(), but without authentication.
        # ping is used to check version before token refresh, so we might not have a valid access token yet.
        # ping endpoint does not required authentication, but (AAP 2.6 at least):
        #   - request is rejected if invalid HTTP basic auth is provided.
        #   - request is accepted if invalid 'Authorization: Bearer ...' is provided.
        timeout = 5
        response = requests.get(
            url=url,
            verify=self.cluster.verify_ssl,
            timeout=timeout,
            headers=self.headers)
        if response is None or not response.ok:
            return None
        response = response.json()
        return response

    def detect_aap_version(self):
        logger.info(f'Checking if is AAP 2.5 ... 2.6 at {self.cluster.base_url}')
        response25 = self.ping("/api/gateway/v1/ping/")
        if response25:
            if response25["version"] == "2.6":
                return ClusterVersionChoices.AAP26
            elif response25["version"] == "2.5":
                return ClusterVersionChoices.AAP25
            else:
                raise Exception(f'Not valid version {response25["version"]} for cluster {self.cluster.base_url}.')

        logger.info(f'Checking if is AAP 2.4 at {self.cluster.base_url}')
        response24 = self.ping("/api/v2/ping/")
        if response24:
            return ClusterVersionChoices.AAP24

        raise Exception(f'Not valid version for cluster {self.cluster.base_url}.')

    def check_aap_version(self):
        aap_version = self.detect_aap_version()
        if self.cluster.aap_version != aap_version:
            self.cluster.aap_version = aap_version
            self.cluster.save()
        logger.info(f'Detected AAP version {aap_version} at {self.cluster.base_url}')
        return True

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
