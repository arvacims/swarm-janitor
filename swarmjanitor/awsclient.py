from typing import Dict

from boto3 import Session


class JanitorAwsClient:

    @staticmethod
    def request_auth_token() -> str:
        token_dict = _new_session().client('ecr').get_authorization_token()
        return token_dict['authorizationData'][0]['authorizationToken']

    @staticmethod
    def discover_possible_manager_nodes(name_filter: str) -> Dict:
        return _new_session().client('ec2').describe_instances(
            Filters=[
                {'Name': 'tag:Name', 'Values': [name_filter]},
                {'Name': 'instance-state-name', 'Values': ['running']}
            ]
        )


def _new_session() -> Session:
    return Session()
