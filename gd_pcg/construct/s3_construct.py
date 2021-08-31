import os
import configparser
from aws_cdk import (
    aws_s3 as _s3,
    core
)

class S3Construct(core.Construct):

    def read_config(self,part,name):
        """
        :part: which part in conf, ["config","url"]
        :name: config name
        :return: config value
        """
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        print(path)
        conf= configparser.ConfigParser()
        conf.read(os.path.join(path, "construct/app.conf"))
        value = conf.get(part,name)
        print(value)
        return value

    def __init__(self,scope:core.Construct,id:str,Stage="default",**kwargs):
        super().__init__(scope, id, **kwargs)
        self.buckets = {}

        # import existed s3 bucket

        self.result_bucket = _s3.Bucket.from_bucket_name(
            self,
            'result',
            bucket_name = self.read_config("config",'result-bucket')
        )

        
        self.buckets['result'] = self.result_bucket
    def get_s3_bucket(self,name):
        return self.buckets[name]
