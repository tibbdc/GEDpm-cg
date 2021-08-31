# -*- coding:utf-8 -*-

import boto3
import os
import json
import uuid
import datetime
import re

s3 = boto3.resource('s3')

def check(filename):
    index = 0
    num = 0
    # all number
    cmd = 'grep ">" '+ filename +" | wc -l"
    all_num = os.popen(cmd).read().strip()
    print(all_num)
    try:
        with open(filename,encoding="utf-8") as f:
            for i in f:
                if index == 0:
                    if not i.startswith(">"):
                        print("upload file is not fasta file")
                        return {
                            "statusCode":400,
                            "res":"filetype error,please add queryid"
                        }
                    elif i.startswith(">"):
                        num += 1
                elif index >= 10000:
                    break
                else:
                    if i.startswith(">"):
                        num += 1
                        continue
                    else:
                        m = re.match(
                            r"[ARNDCQEGHILKMFPSTWYVNX]*",
                            i.strip(),
                            re.I
                        )
                        if len(m.group()) == len(i.strip()):
                            print('%s matched' % i.strip())
                        else:
                            print('%s error' % i.strip())
                            return {
                                "statusCode":400,
                                "res":"%s not match, please check" % i.strip()
                            }
                index +=1
        return {
            "statusCode":200,
            "number":str(all_num)
            }

    except Exception as e:
        print(e)
        return {
            "statusCode":500,
            "res":str(e)
        }
    
def lambda_handler(event,context):
    """
        event = {
            "S3_Path":"s3://bucket/obj_key"
        }

    """
    print(event)
    # lambda workdir
    workdir = os.path.join('/tmp',str(uuid.uuid4()))
    os.mkdir(workdir)

    print("---------1.download file from s3--------------")

    bucket = event["S3_Path"].split('/')[2]
    key = '/'.join(event["S3_Path"].split('/')[3:])
    filename = event["S3_Path"].split('/')[-1]
    local_filename = os.path.join(workdir,filename)
    s3.meta.client.download_file(bucket, key, local_filename)

    print("---------2.check download file---------------")
    
    response = check(local_filename)
    os.system("rm -rf "+ workdir)
    return response
