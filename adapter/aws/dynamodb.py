import json
from boto3 import client
from boto3_type_annotations.dynamodb import Client as DynamoDBClient


class DynamoDB:
    def __init__(self,table_name:str):
        self.table_name = table_name
        self.dynamodb:DynamoDBClient = client("dynamodb")
    
    def get_item_by_hash_key(self,key:str):
        item = self.dynamodb.get_item(TableName=self.table_name,Key={
            "KEY": {
                "S": key
            }
        })
        return item
    
    def put_json_item(self,key:str,data:dict):
        item = self.dynamodb.put_item(TableName=self.table_name,Item={
            "KEY": {
                "S": key
            },
            "DATA": {
                "S": json.dumps(data)
            }
        })
        return item
