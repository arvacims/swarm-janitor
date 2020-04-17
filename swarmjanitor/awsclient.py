from typing import Dict, List

from boto3 import Session

from swarmjanitor.utils import flatten_list


class JanitorAwsClient:

    @staticmethod
    def request_auth_token() -> str:
        token_dict = _new_session().client('ecr').get_authorization_token()
        return token_dict['authorizationData'][0]['authorizationToken']

    @staticmethod
    def discover_possible_manager_addresses(name_filter: str) -> List[str]:
        description = _new_session().client('ec2').describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [name_filter]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )

        reservations: List[Dict] = description['Reservations']
        reservation_instances: List[List[Dict]] = [reservation['Instances'] for reservation in reservations]
        instances: List[Dict] = flatten_list(reservation_instances)

        return [instance['PrivateIpAddress'] for instance in instances]


def _new_session() -> Session:
    return Session()
