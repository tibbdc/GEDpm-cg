from aws_cdk import core as cdk
from aws_cdk import core

from gd_pcg.construct.lambda_construct import LambdaConstruct
from gd_pcg.construct.s3_construct import S3Construct
from gd_pcg.construct.dynamodb_construct import DynamodbConstruct
from gd_pcg.construct.apigateway_construct import APIConstruct
from gd_pcg.construct.stepfunction_construct import SfnConstruct
from gd_pcg.construct.iam_construct import IamConstruct


class GdPcgStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, construct_id: str,Stage="default", **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        # Definition of s3 
        self.My_S3_Bucket = S3Construct(
            self,
            "s3-"+Stage
        )

        # Definition of dynamodb 
        self.My_dynamodb_table = DynamodbConstruct(
            self,
            "dynamodb-"+Stage
        )

        # Definition of lambda
        self.My_Lambda_Func = LambdaConstruct(
            self,
            "lambda-"+Stage,
            TargetS3 = self.My_S3_Bucket,
            TargetDdb = self.My_dynamodb_table
        )

        # Definiton of step function
        self.My_Step_Function = SfnConstruct(
            self,
            "stepfunction-"+Stage,
            TargetLambda = self.My_Lambda_Func,
            TargetS3 = self.My_S3_Bucket
        )

        # Definiton of API Gateway
        self.My_API_Gateway = APIConstruct(
            self,
            "apigateway-"+ Stage,
            TargetLambda = self.My_Lambda_Func,
            TargetDdb = self.My_dynamodb_table,
            TargetSfn = self.My_Step_Function,
            TargetS3 = self.My_S3_Bucket
        )

        # Definition of IAM
        self.My_Iam = IamConstruct(
            self,
            "Iam-construct",
            TargetS3 = self.My_S3_Bucket,
            TargetApiGateway = self.My_API_Gateway
        )
