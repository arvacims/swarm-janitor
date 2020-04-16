from boto3 import Session


class JanitorAwsClient:

    @staticmethod
    def _new_session() -> Session:
        return Session()

    @staticmethod
    def request_auth_token() -> str:
        token_dict = JanitorAwsClient._new_session().client('ecr').get_authorization_token()
        return token_dict['authorizationData'][0]['authorizationToken']
