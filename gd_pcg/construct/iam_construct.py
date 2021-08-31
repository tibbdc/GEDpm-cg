import os

from aws_cdk import (
    aws_s3 as _s3,
    aws_iam as iam,
    core,
)

class IamConstruct(core.Construct):
    def __init__(self,scope:core.Construct,id:str,TargetS3="default",TargetApiGateway="default",**kwargs):
        super().__init__(scope, id, **kwargs)

        # auth user upload to s3  iam policy
        auth_user_upload_policy = iam.ManagedPolicy(self, "user-upload-s3-policy",
            statements=[
                iam.PolicyStatement(
                    actions=["s3:GetObject","s3:PutObject","s3:DeleteObject"],
                    effect=iam.Effect.ALLOW,
                    resources=[TargetS3.get_s3_bucket('result').bucket_arn + "/public/*"]
                )
            ]
        )

        # user invoke api
        user_invoke_api_policy = iam.ManagedPolicy(self, "user-allow-api-policy",
            statements=[
                iam.PolicyStatement(
                    actions=["execute-api:Invoke"],
                    effect=iam.Effect.ALLOW,
                    resources=TargetApiGateway.get_method_arns()
                )
            ]
        )

        # output policy name 
        core.CfnOutput(
            self,
            "auth user upload s3 policy",
            value=auth_user_upload_policy.managed_policy_name
        )

        core.CfnOutput(
            self,
            "invoke api",
            value=user_invoke_api_policy.managed_policy_name
        )
