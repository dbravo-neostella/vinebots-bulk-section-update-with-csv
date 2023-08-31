import json
import boto3

SSM_CLIENT = boto3.client("secretsmanager")


def get_secret(secret_name):
    """Retrieves a single secret from SecretsManager.

    Parameters:
        - secret_name (str): Name of the secret to be retrieved.

    Returns:
        - A string representing the value of interest.
    """
    secret_response = SSM_CLIENT.get_secret_value(SecretId=secret_name)
    secret_json = json.loads(secret_response["SecretString"])

    return secret_json
