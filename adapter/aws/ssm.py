from loguru import logger
from boto3.session import Session
from boto3_type_annotations.ssm import Client as SSMClient
from botocore.exceptions import ClientError
import util


class SSM:
    def __init__(self, session: Session):
        """
        Initialize the SSM class with the specified AWS region.

        Parameters:
        - region_name (str): The AWS region to use (default is 'us-east-1').
        """
        self.ssm_client: SSMClient = session.client("ssm")

    @util.time_track(description="downloading parameter from SSM")
    def get_parameter(self, parameter_name, with_decryption=False):
        """
        Retrieve a parameter value from AWS Systems Manager (SSM) Parameter Store.

        Parameters:
        - parameter_name (str): The name of the parameter.
        - with_decryption (bool): Whether to decrypt the parameter value (default is False).

        Returns:
        - str: The parameter value.
        """
        logger.info(f"loading {parameter_name}")
        try:
            response = self.ssm_client.get_parameter(
                Name=parameter_name, WithDecryption=with_decryption
            )
            return response["Parameter"]["Value"]
        except ClientError as e:
            if e.response["Error"]["Code"] == "ParameterNotFound":
                raise ValueError(f"Parameter '{parameter_name}' not found.") from e
            else:
                raise RuntimeError(
                    f"Error retrieving parameter '{parameter_name}': {e}"
                ) from e
