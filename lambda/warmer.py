import os
import json
import asyncio
import aioboto3
from loguru import logger


FUNCTION_NAME = os.environ.get("FUNCTION_NAME")
HEALTH_CHECK_PATH = os.environ.get("HEALTH_CHECK_PATH")
COUNT = int(os.environ.get("COUNT"))


async def _invoke_lambda(client):
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
    response = await client.invoke(
        FunctionName=FUNCTION_NAME,
        InvocationType="RequestResponse",
        Payload=json.dumps(payload),
    )

    if response.get("StatusCode") == 200:
        # Get the response payload
        response_payload = json.loads(await response["Payload"].read())
        logger.info(response_payload)
        return response_payload

    return None


async def trigger_lambda_invocation():
    session = aioboto3.Session()
    async with session.client("lambda") as client:
        try:
            tasks = []
            for _ in range(COUNT):
                task = asyncio.ensure_future(_invoke_lambda(client))
                tasks.append(task)

            responses = await asyncio.gather(*tasks)
            return {"statusCode": 200, "body": json.dumps(responses)}
        except Exception as e:
            return {"statusCode": 500, "body": json.dumps(str(e))}


def handler(event, context):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(trigger_lambda_invocation())


if __name__ == "__main__":
    asyncio.run(trigger_lambda_invocation())
