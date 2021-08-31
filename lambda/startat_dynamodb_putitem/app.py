# description: create submit id item in dynamodb table

import boto3
import subprocess
import uuid
import os
import json
import datetime
import time
# enviroment
region = os.environ["AWS_DEFAULT_REGION"]

dynamodb = boto3.resource('dynamodb',region_name=os.environ['AWS_DEFAULT_REGION'])
output_table = dynamodb.Table(os.environ['ddbOutput'])

# expired seconds
day = 7
seconds = day * 60 * 60 * 24
# seconds = 120

def create_ID_item(table,orderid,submitime,name):
    try:
        table.put_item(
            Item={
                "PK":orderid,
                "Timestamp":submitime,
                "ExpirationTime":int(time.time()) + seconds,
                "Status":"running",
                "Name":name,
                "Result":"",
                "Error":""
            }
        )
        print('%s insert into output table' % orderid)
    except Exception as e:
        print(e)


def lambda_handler(event,context):
    print(event)
    try:
        create_ID_item(
            output_table,
            event["ID"],
            event["Timestamp"],
            event["s3_sequence_file"].split('/')[-1],
            )
    except Exception as e:
        print(e)
