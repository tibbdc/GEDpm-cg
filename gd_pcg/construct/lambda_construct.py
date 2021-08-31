import os
import configparser

from aws_cdk import (
    aws_lambda as _lambda,
    aws_lambda_event_sources as _lambda_event_sources,
    aws_iam as iam,
    core,
)

class LambdaConstruct(core.Construct):

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
    
    def __init__(self,scope:core.Construct,id:str,TargetS3 = "default",TargetDdb = "default",**kwargs):
        super().__init__(scope, id, **kwargs)

        self.lambda_functions = {}
        # lambda role
        self.lambda_role = iam.Role(
            self,
            "lambda-role",
            assumed_by = iam.ServicePrincipal(
                "lambda.amazonaws.com"
            )
        )
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=['logs:CreateLogGroup','logs:CreateLogStream','logs:PutLogEvents',"s3:PutObjectAcl"],
                resources=["*"]
            )
        )
        # access to s3
        TargetS3.get_s3_bucket("result").grant_read_write(self.lambda_role)
        

        # access to dynamodb table
        TargetDdb.get_dynamodb_tables('output').grant_full_access(self.lambda_role)
        
        # layers
        # primer3
        primer3_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "import existed primer3",
            layer_version_arn = self.read_config("layer","primer3")
        )
        # zip
        zip_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "import existed zip",
            layer_version_arn = self.read_config("layer","zip")
        )
        # blastn
        blastn_layer = _lambda.LayerVersion.from_layer_version_arn(
            self,
            "import existed blastn",
            layer_version_arn = self.read_config("layer","blastn")
        )

        # startat dynamodb putitem
        self.startat_dynamodb_putitem = _lambda.Function(
            self,
            "startat_putitem",
            runtime =_lambda.Runtime.PYTHON_3_8,
            code = _lambda.Code.asset('lambda/startat_dynamodb_putitem/'),
            role=self.lambda_role,
            handler="app.lambda_handler",
            timeout=core.Duration.seconds(60),
            environment={
                "ddbOutput":TargetDdb.get_dynamodb_tables('output').table_name
            }
        )

        # GDPcg lambda function
        self.GDPcg_lambda = _lambda.Function(
            self,
            "GDPcg",
            runtime =_lambda.Runtime.PYTHON_3_8,
            code = _lambda.Code.asset('lambda/GDPcg/'),
            role=self.lambda_role,
            handler="app.lambda_handler",
            timeout=core.Duration.seconds(900),
            memory_size=3000,
            layers = [primer3_layer,zip_layer,blastn_layer],
            environment={
                "s3Result":TargetS3.get_s3_bucket("result").bucket_name,
                "ddbOutput":TargetDdb.get_dynamodb_tables('output').table_name
                
            }
        )

        # result lambda function
        self.result_lambda = _lambda.Function(
            self,
            "result",
            runtime =_lambda.Runtime.PYTHON_3_8,
            code = _lambda.Code.asset('lambda/result/'),
            role=self.lambda_role,
            handler="app.lambda_handler",
            timeout=core.Duration.seconds(30),
            memory_size=128,
            environment={
                "ddbOutput":TargetDdb.get_dynamodb_tables('output').table_name,
                "s3Result":TargetS3.get_s3_bucket("result").bucket_name,
            }
        )

        #############################################
        # ddb stream lambda
        # according to system records stream, delete the expiredTime item  # s3 data file after 7 days
        self.ddb_stream_lambda = _lambda.Function(
            self,
            "ddb_stream",
            runtime =_lambda.Runtime.PYTHON_3_8,
            # code = _lambda.Code.asset('lambda/ddb_stream_lambda/'),
            code = _lambda.Code.asset('lambda/ddb_stream/'),
            role=self.lambda_role,
            handler="app.lambda_handler",
            timeout=core.Duration.seconds(60),
            environment={
                "ddbOutput":TargetDdb.get_dynamodb_tables('output').table_name,
                "s3Result":TargetS3.get_s3_bucket("result").bucket_name,
            }
        )
        # dynamodb stream source event
        self.ddb_stream_lambda.add_event_source(
            _lambda_event_sources.DynamoEventSource(
                TargetDdb.get_dynamodb_tables('output'),
                batch_size=100,
                starting_position = _lambda.StartingPosition.TRIM_HORIZON,
                bisect_batch_on_error =True,
                retry_attempts = 10
            )
        )

        # # check lambda function
        # self.check_lambda = _lambda.Function(
        #     self,
        #     "check",
        #     runtime =_lambda.Runtime.PYTHON_3_8,
        #     code = _lambda.Code.asset('lambda/check/'),
        #     role=self.lambda_role,
        #     handler="app.lambda_handler",
        #     timeout=core.Duration.seconds(30),
        #     memory_size=128,
        #     environment={
        #         "s3Result":TargetS3.get_s3_bucket("result").bucket_name,

        #     }
        # )

        self.lambda_functions['startat_dynamodb_putitem'] = self.startat_dynamodb_putitem
        self.lambda_functions["result"] = self.result_lambda
        self.lambda_functions["GDPcg"] = self.GDPcg_lambda
        # self.lambda_functions["check"] = self.check_lambda
    def get_lambda_functions(self,name):
        return self.lambda_functions[name]
