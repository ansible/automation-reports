import datetime
import json
import logging
from urllib.parse import urlsplit

import pytz
import requests
import urllib3
from django.conf import settings
from django.db import transaction
from requests.auth import HTTPBasicAuth

from backend.apps.clusters.encryption import decrypt_value, encrypt_value
from backend.apps.clusters.models import (
    ClusterSyncData,
    ClusterSyncStatus,
    JobTemplate,
    Job,
    Organization, ClusterVersionChoices
)
from backend.apps.clusters.schemas import ClusterSchema

logger = logging.getLogger("automation-reports.clusters.connector")


class ApiConnector:

    def __init__(self,
                 cluster: ClusterSchema,
                 timeout=30,
                 since: datetime.datetime | None = None,
                 until: datetime.datetime | None = None,
                 managed: bool = False):

        logger.info(f"Initializing ApiConnector for cluster: {cluster.__str__()}")
        if not settings.SHOW_URLLIB3_INSECURE_REQUEST_WARNING:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        self.cluster = cluster
        self.timeout = timeout
        self.managed = managed

        self.access_token = decrypt_value(cluster.access_token)
        logger.debug(f"Access token decrypted for cluster: {cluster.__str__()}")

        try:
            cluster_sync_data = ClusterSyncStatus.objects.get(cluster=self.cluster)
            logger.info("ClusterSyncStatus found for cluster.")
        except ClusterSyncStatus.DoesNotExist:
            logger.warning("ClusterSyncStatus not found, creating new.")
            cluster_sync_data = ClusterSyncStatus(cluster=self.cluster)
        self.cluster_sync_data = cluster_sync_data

        self.until = until

        if self.managed:
            self.since = since
            logger.debug("Managed mode: using provided since value.")
        else:
            if since is not None:
                self.since = since
                logger.debug("Since value provided, using it.")
            elif self.cluster_sync_data.last_job_finished_date is not None and self.managed is False:
                self.since = self.cluster_sync_data.last_job_finished_date
                logger.debug("Using last_job_finished_date from sync data.")
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
                        logger.debug("Parsed INITIAL_SYNC_SINCE from settings.")
                    except ValueError:
                        logger.warning("Failed to parse INITIAL_SYNC_SINCE, using fallback.")
                        _date = None
                if _date is None:
                    _date = datetime.datetime.now(pytz.UTC) - datetime.timedelta(days=initial_sync_days)
                    logger.debug("Using fallback initial sync date.")
                self.since = datetime.datetime.combine(_date.astimezone(pytz.UTC),
                                                       datetime.datetime.min.time()).astimezone(pytz.UTC)
                logger.info(f"Initial sync since: {self.since}")

    @property
    def headers(self):
        logger.debug("Generating request headers.")
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    def _reauthorize(self, timeout=None):
        logger.info("Starting token refresh process.")
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
        auth = HTTPBasicAuth(client_id, client_secret)
        logger.debug(f"Token refresh POST data: {data}")
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
            logger.error(
                f'Token refresh POST request failed with status {response.status_code} url={url}, text={json.dumps(response.text)}')
            return False
        logger.info(f'Token refresh POST request succeeded with status {response.status_code}')
        resp = response.json()

        self.cluster.access_token = encrypt_value(resp['access_token'])
        self.cluster.refresh_token = encrypt_value(resp["refresh_token"])
        self.access_token = resp['access_token']
        self.cluster.save()
        logger.debug("Cluster tokens updated and saved.")

        return True

    def _get_request(self, url, timeout=None):
        return requests.get(
            url=url,
            verify=self.cluster.verify_ssl,
            timeout=timeout if timeout is not None else self.timeout,
            headers=self.headers)

    def _get_with_reauth(self, url, timeout=None):
        # try 1st time
        try:
            response = self._get_request(url, timeout)
        except requests.exceptions.ConnectionError as e:
            # begin mock testing block ------------------------
            # "return None" makes code behave like all is OK, and AAP returned empty json ("{}").
            # The responses library tries to tell mock for an URL is missing via ConnectionError,
            # but this hides the exception, and tests might pass when they should fail.
            # Reraise responses generated ConnectionError.
            e_inner = e.args[0]
            if isinstance(e_inner, str) and e_inner.startswith("Connection refused by Responses - "):
                raise
            # end mock testing block ------------------------
        except requests.exceptions.RequestException as e:
            logger.error(f'GET request failed with exception {e}')
            return None
        logger.debug(f"First GET response status: {response.status_code}")
        if response.ok:
            return response

        logger.error(f'GET request failed with status {response.status_code}')
        if response.status_code != 401:
            return response
        logger.info("401 received, attempting re-authentication.")
        self._reauthorize()

        try:
            response = self._get_request(url, timeout)
        except requests.exceptions.RequestException as e:
            logger.error(f'GET request failed with exception {e}')
            return None
        logger.debug(f"Second GET response status: {response.status_code}")
        return response

    def execute_get_one(self, url, timeout=None):
        logger.info(f'Executing GET request to {url}')
        response = self._get_with_reauth(url, timeout=timeout)
        if response is None or not response.ok:
            logger.warning(f"GET request to {url} failed or returned no response.")
            return None
        product_name = response.headers.get("X-Api-Product-Name", None)
        logger.debug(f"Product name from headers: {product_name}")
        if product_name is None or product_name == "AWX":
            logger.error("Not supported product.")
            raise Exception("Not supported product.")
        response = response.json()
        logger.debug(f"GET response JSON: {response}")
        return response

    def execute_get(self, endpoint):
        logger.info(f"Executing paginated GET for endpoint: {endpoint}")
        _next = endpoint
        results = []
        while _next is not None:
            url = f'{self.cluster.base_url}{_next}'
            logger.debug(f"Paginated GET request to {url}")
            response = self.execute_get_one(url)
            if response:
                next_page = response.get('next', None)
                results = response.get('results', response)
                logger.debug(f"Next page: {next_page}")
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
        logger.info("Fetching jobs for cluster.")
        parameters = ""
        if self.since is not None:
            since = self.since.isoformat().replace('+00:00', 'Z')
            parameters += f'&finished__gt={since}'
        if self.until is not None:
            until = self.until.isoformat().replace('+00:00', 'Z')
            parameters += f'&finished__lte={until}'
        endpoint = f'{self.cluster.api_url}/jobs/?page_size=100&page=1&order_by=finished{parameters}'
        logger.debug(f"Jobs endpoint: {endpoint}")
        response = self.execute_get(endpoint)
        for results in response:
            for result in results:
                logger.debug(f"Yielding job: {result.get('id')}")
                yield result

    def job_host_summaries(self, job_id):
        logger.info(f"Fetching host summaries for job {job_id}")
        endpoint = f'{self.cluster.api_url}/jobs/{job_id}/job_host_summaries?page_size=100&page=1&order_by=modified'
        response = self.execute_get(endpoint)
        for results in response:
            for result in results:
                logger.debug(f"Yielding host summary: {result.get('id')}")
                yield result

    def sync_common(self, sync_type):
        logger.info(f"Starting sync_common for type: {sync_type}")
        if sync_type == 'organization':
            endpoint = f'{self.cluster.api_url}/organizations/?page_size=100&page=1'
            qs = Organization.objects.filter(cluster=self.cluster)
        elif sync_type == 'job_template':
            endpoint = f'{self.cluster.api_url}/job_templates/?page_size=200&page=1'
            qs = JobTemplate.objects.filter(cluster=self.cluster)
        else:
            logger.error(f"Sync type {sync_type} not implemented.")
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
                logger.debug(f"Processing item: {result['id']}")
                if sync_type == 'job_template':
                    external_organization = result.get("summary_fields", {}).get("organization", {}).get("id", None)
                    if external_organization:
                        organization = db_organizations.get(external_organization, None)
                    else:
                        organization = None
                else:
                    organization = None

                if db_item is not None:
                    logger.info(f"Updating {sync_type} {db_item.name}")
                    db_item.name = result["name"]
                    db_item.description = result["description"]
                    if sync_type == 'job_template':
                        db_item.organization = organization
                    db_item.save()
                else:
                    logger.info(f"Creating new {sync_type} {result['name']}")
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
        timeout = 5
        try:
            response = requests.get(
                url=url,
                verify=self.cluster.verify_ssl,
                timeout=timeout,
                headers=self.headers)
        except requests.exceptions.RequestException as e:
            logger.error(f"Ping request failed: {e}")
            return None
        if response is None or not response.ok:
            logger.warning(f"Ping to {url} failed or returned no response.")
            return None
        response = response.json()
        logger.debug(f"Ping response: {response}")
        return response

    def detect_aap_version(self):
        logger.info(f'Checking if is AAP 2.5 ... 2.6 at {self.cluster.base_url}')
        response25 = self.ping("/api/gateway/v1/ping/")
        if response25:
            logger.debug(f"AAP 2.5/2.6 ping response: {response25}")
            if response25["version"] == "2.6":
                return ClusterVersionChoices.AAP26
            elif response25["version"] == "2.5":
                return ClusterVersionChoices.AAP25
            else:
                logger.error(f'Not valid version {response25["version"]} for cluster {self.cluster.base_url}.')
                raise Exception(f'Not valid version {response25["version"]} for cluster {self.cluster.base_url}.')

        logger.info(f'Checking if is AAP 2.4 at {self.cluster.base_url}')
        response24 = self.ping("/api/v2/ping/")
        if response24:
            logger.debug(f"AAP 2.4 ping response: {response24}")
            return ClusterVersionChoices.AAP24

        logger.error(f'Not valid version for cluster {self.cluster.base_url}.')
        raise Exception(f'Not valid version for cluster {self.cluster.base_url}.')

    def check_aap_version(self):
        logger.info("Checking AAP version for cluster.")
        aap_version = self.detect_aap_version()
        if self.cluster.aap_version != aap_version:
            logger.info(f"Updating cluster version from {self.cluster.aap_version} to {aap_version}")
            self.cluster.aap_version = aap_version
            self.cluster.save()
        logger.info(f'Detected AAP version {aap_version} at {self.cluster.base_url}')
        return True

    def sync_jobs(self):
        logger.info("Starting job sync.")
        for job in self.jobs:
            logger.info("Checking status of job %s", job)
            job_id = job.get("id", None)
            finished = job.get("finished", None)
            if job_id is None or finished is None:
                logger.warning(f"Missing id or finished date time in job: {job}")
                continue
            try:
                finished = datetime.datetime.fromisoformat(finished).astimezone(datetime.timezone.utc)
            except ValueError:
                logger.error(f"Invalid finished date format for job: {finished}")
                raise TypeError(f"finished must be of type datetime.datetime job: {finished}")

            job["host_summaries"] = []
            logger.info(f"Job {job_id} retrieving host summaries.")

            for host_summary in self.job_host_summaries(job_id):
                logger.debug(f"Appending host summary for job {job_id}: {host_summary.get('id')}")
                job["host_summaries"].append(host_summary)

            with transaction.atomic():
                logger.info(f"Job {job_id} saving data.")
                self.cluster_sync_data.last_job_finished_date = finished if self.cluster_sync_data.last_job_finished_date is None or finished > self.cluster_sync_data.last_job_finished_date else self.cluster_sync_data.last_job_finished_date
                self.cluster_sync_data.save()
                ClusterSyncData.objects.create(cluster=self.cluster, data=job)
                logger.debug(f"Job {job_id} data saved.")
