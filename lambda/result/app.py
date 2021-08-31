import boto3
import subprocess
import uuid
import os
import json
import datetime
import time

# enviroment
region = os.environ["AWS_DEFAULT_REGION"]
s3 = boto3.resource('s3')
dynamodb = boto3.resource('dynamodb',region_name=os.environ['AWS_DEFAULT_REGION'])
output_table = dynamodb.Table(os.environ['ddbOutput'])


def get_id_item(table,key):
    """
    :table: database table dynamodb handler
    :key: the key
    :return: if exists, return the sequence id. if not exists, return false
    """
    response = table.get_item(
            Key={
                "PK":key,
                }
        )
    print(response)
    if 'Item' in response:
        # 返回ExpiredTime > time.time当前时间的item
        # if response["Item"]["ExpirationTime"] > int(time.time()):
        infos = {
            "ID":response["Item"]["PK"],
            "Status":response["Item"]["Status"],
            "Error":response["Item"]["Error"],
            "Timestamp":response["Item"]["Timestamp"],
            "Result":response["Item"]["Result"],
            "Name":response["Item"]["Name"]
        }
        return infos
        # else:
        #     return False
    else:
        return False
def lambda_handler(event,context):
    """


    """
    print(event)
    dictall = []
    for i in event["ids"]:
        res = get_id_item(output_table,i)
        if res:
            dictall.append(res)
    return {
        "statusCode":200,
        "Items":dictall
    }
