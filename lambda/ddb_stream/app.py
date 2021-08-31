import boto3
import os

# enviroment
region = os.environ["AWS_DEFAULT_REGION"]
# s3 = boto3.resource('s3')
s3 = boto3.client('s3')

result_bucket = os.environ["s3Result"]
html_bucket = os.environ["s3Html"]
def get_all_s3_objects(s3, **base_kwargs):
    continuation_token = None
    while True:
        list_kwargs = dict(MaxKeys=1000, **base_kwargs)
        if continuation_token:
            list_kwargs['ContinuationToken'] = continuation_token
        response = s3.list_objects_v2(**list_kwargs)
        yield from response.get('Contents', [])
        if not response.get('IsTruncated'):  # At the end of the list?
            break
        continuation_token = response.get('NextContinuationToken')

def handle_remove(record):
    print('Handling REMOVE event')
    #1. parse oldimage and price
    old_image = record['dynamodb']['OldImage']
    submitid = old_image['PK']['S']
    #2. remove output s3 data
    #2.1 remove output s3 data
    for object_file in get_all_s3_objects(s3,Bucket=result_bucket, Prefix=os.path.join("output",submitid+'/'),Delimiter='/'):
        print('Deleting', object_file['Key'])
        s3.delete_object(Bucket=result_bucket, Key=object_file['Key'])

def lambda_handler(event,context):
    """

    """
    print('------------1-------------')
    print(event)
    try:
        #1. Iterate over each record
        for record in event["Records"]:
            if record['eventName']  == "REMOVE":
                handle_remove(record)

        print('------------2-------------')
    except Exception as e:
        print(e)
        print('------------3-------------')

