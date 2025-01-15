from abc import ABC
from backend.apps.instances.schemas import InstanceSchema
import requests

class Connector(ABC):

    def __init__(self, instance: InstanceSchema, timeout=30):
        self.instance = instance
        self.timeout = timeout

    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self.instance.access_token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }

    @property
    def base_url(self):
        return f'{self.instance.protocol}://{self.instance.host}:{self.instance.port}'

    @property
    def ping(self):
        print(self.base_url)
        endpoint = '/api/v2/ping/'
        url = f'{self.base_url}{endpoint}'
        print(url)
        try:
            response = requests.get(
                url=url,
                verify=self.instance.verify_ssl,
                timeout=self.timeout,
                headers=self.headers)
        except requests.exceptions.RequestException as e:
            return None
        if response.status_code != 200:
            return None
        return response.json()
