import os
import configparser

from aws_cdk import (
    aws_s3 as _s3,
    aws_dynamodb as ddb,
    core
)


class DynamodbConstruct(core.Construct):

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

        self.dynamodb_tables = {}

        self.output_table = ddb.Table.from_table_attributes(
            self,
            "import output table",
            table_name = self.read_config("config",'result-table'),
            table_stream_arn=self.read_config("config","result-table-stream-arn")
        )
        self.dynamodb_tables["output"] = self.output_table
    def get_dynamodb_tables(self,name):
        return self.dynamodb_tables[name]
