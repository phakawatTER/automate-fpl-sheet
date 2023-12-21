import json
from boto3_type_annotations.stepfunctions import Client as SFNClient
from boto3.session import Session


class StateMachine:
    def __init__(self, session: Session):
        self.__sfn: SFNClient = session.client("stepfunctions")

    def start_execution(self, state_machine_arn: str, input_data: dict):
        input_json = json.dumps(input_data)
        try:
            response = self.__sfn.start_execution(
                stateMachineArn=state_machine_arn, input=input_json
            )
            return response
        except Exception as e:
            raise Exception(f"Error calling SFN to start execution: {str(e)}") from e
