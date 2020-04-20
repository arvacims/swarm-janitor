from typing import Dict, List

from boto3 import Session

from swarmjanitor.utils import flatten_list


class JanitorAwsClient:
    _session: Session

    def __init__(self):
        self.refresh_session()

    def refresh_session(self):
        self._session = Session()

    def request_auth_token(self) -> str:
        token_dict = self._session.client('ecr').get_authorization_token()
        return token_dict['authorizationData'][0]['authorizationToken']

    def discover_possible_manager_addresses(self, name_filter: str) -> List[str]:
        description = self._session.client('ec2').describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [name_filter]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        reservations: List[Dict] = description['Reservations']
        reservation_instances: List[List[Dict]] = [reservation['Instances'] for reservation in reservations]
        instances: List[Dict] = flatten_list(reservation_instances)

        return [instance['PrivateIpAddress'] for instance in instances]
