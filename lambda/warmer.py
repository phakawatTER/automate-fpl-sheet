import os
import json
import boto3
from boto3_type_annotations.lambda_ import Client as LambdaClient

FUNCTION_NAME = os.environ.get("FUNCTION_NAME")
HEALTH_CHECK_PATH = os.environ.get("HEALTH_CHECK_PATH")
COUNT = int(os.environ.get("COUNT"))

def handler(event, context):
    # Get the payload from the event
    payload = {
        "httpMethod": "GET",
        "path": HEALTH_CHECK_PATH,
        "resource": "/{proxy+}",
        "queryStringParameters": None,
        "requestContext": {},
        "body": None,
    }

    # Initialize the Lambda client
    client:LambdaClient = boto3.client('lambda')

    # Invoke the Lambda function synchronously
    try:
        for __i in range(COUNT):
            response = client.invoke(
                FunctionName=FUNCTION_NAME,
                InvocationType='RequestResponse',
                Payload=json.dumps(payload)
            )
            if response.get('StatusCode') == 200:
                # Get the response payload
                response = json.loads(response['Payload'].read())
                print(response)
        return {
            'statusCode': 200,
            'body': json.dumps(response)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
