import os
import json

from aws_cdk import (
    aws_iam as iam,
    aws_apigateway as apigw,
    core,
)

class APIConstruct(core.Construct):

    def __init__(self,scope:core.Construct,id:str,TargetLambda="default",TargetDdb="default",TargetSfn="default",TargetS3="default",**kwargs):
        super().__init__(scope, id, **kwargs)

        self._method_arns = []
        # api role
        # IAM role
        self.api_role = iam.Role(
            self,
            "api_role",
            assumed_by = iam.ServicePrincipal(
                "apigateway.amazonaws.com"
            )
        )

        # root api gateway endpoint  
        self._api = apigw.RestApi(
            self, 
            'GDPcg'
            )
        
        # statemachine grant access for api role
        TargetSfn.get_step_functions("GDPcg").grant_start_execution(self.api_role)

        # access to dynamodb
        TargetDdb.get_dynamodb_tables("output").grant_read_data(self.api_role)


        # resources
        entity_GDPcg = self._api.root.add_resource('GDPcg')
        # GDPcg entity
        # post
        # api gateway + stepfunction
        GDPcg_post_intergration_options = apigw.IntegrationOptions(
            credentials_role=self.api_role,
            integration_responses=[
            {
                'statusCode': '200',
                'responseParameters': {
                'method.response.header.Access-Control-Allow-Origin': "'*'",
                }
            }
                ],
            request_templates={
                'application/json': json.dumps({
                    "stateMachineArn":TargetSfn.get_step_functions("GDPcg").state_machine_arn,
                    "input":json.dumps({
                        "ID": "$input.path('$').ID",
                        "Timestamp": "$input.path('$').Timestamp",
                        "database": "$input.path('$').database",
                        "user_upload_database": "$input.path('$').user_upload_database",
                        "s3_sequence_file": "$input.path('$').s3_sequence_file",
                        "s3_plasmid_file": "$input.path('$').s3_plasmid_file",
                        "max_left_arm_seq_length": "$input.path('$').max_left_arm_seq_length",
                        "min_left_arm_seq_length": "$input.path('$').min_left_arm_seq_length",
                        "max_right_arm_seq_length": "$input.path('$').max_right_arm_seq_length",
                        "min_right_arm_seq_length": "$input.path('$').min_right_arm_seq_length",
                        "max_verify_1_up_ponit": "$input.path('$').max_verify_1_up_ponit",
                        "min_verify_1_up_ponit": "$input.path('$').min_verify_1_up_ponit",
                        "max_verify_1_down_ponit": "$input.path('$').max_verify_1_down_ponit",
                        "min_verify_1_down_ponit": "$input.path('$').min_verify_1_down_ponit",
                        "max_verify_2_down_ponit": "$input.path('$').max_verify_2_down_ponit",
                        "min_verify_2_down_ponit": "$input.path('$').min_verify_2_down_ponit",
                        "left_arm_primer_opt_tm": "$input.path('$').left_arm_primer_opt_tm",
                        "left_arm_primer_min_tm": "$input.path('$').left_arm_primer_min_tm",
                        "left_arm_primer_max_tm": "$input.path('$').left_arm_primer_max_tm",
                        "left_arm_primer_min_gc": "$input.path('$').left_arm_primer_min_gc",
                        "left_arm_primer_max_gc": "$input.path('$').left_arm_primer_max_gc",
                        "right_arm_primer_opt_tm": "$input.path('$').right_arm_primer_opt_tm",
                        "right_arm_primer_min_tm": "$input.path('$').right_arm_primer_min_tm",
                        "right_arm_primer_max_tm": "$input.path('$').right_arm_primer_max_tm",
                        "right_arm_primer_min_gc": "$input.path('$').right_arm_primer_min_gc",
                        "right_arm_primer_max_gc": "$input.path('$').right_arm_primer_max_gc",
                        "verify_1_primer_opt_tm": "$input.path('$').verify_1_primer_opt_tm",
                        "verify_1_primer_min_tm": "$input.path('$').verify_1_primer_min_tm",
                        "verify_1_primer_max_tm": "$input.path('$').verify_1_primer_max_tm",
                        "verify_1_primer_min_tm": "$input.path('$').verify_1_primer_min_tm",
                        "verify_1_primer_min_gc": "$input.path('$').verify_1_primer_min_gc",
                        "verify_1_primer_max_gc": "$input.path('$').verify_1_primer_max_gc",
                        "verify_2_primer_opt_tm": "$input.path('$').verify_2_primer_opt_tm",
                        "verify_2_primer_min_tm": "$input.path('$').verify_2_primer_min_tm",
                        "verify_2_primer_max_tm": "$input.path('$').verify_2_primer_max_tm",
                        "verify_2_primer_min_gc": "$input.path('$').verify_2_primer_min_gc",
                        "verify_2_primer_max_gc": "$input.path('$').verify_2_primer_max_gc"
                    })
                })
            }
            )
        # GDPcg post 
        GDPcg_post_integration = apigw.AwsIntegration(
            service="states",
            action="StartExecution",
            options=GDPcg_post_intergration_options
            )
        GDPcg_post_method = entity_GDPcg.add_method(
            'POST',
            GDPcg_post_integration,
            authorization_type=apigw.AuthorizationType.IAM,
            method_responses=[{
                    'statusCode': '200',
                    'responseParameters': {
                        'method.response.header.Access-Control-Allow-Origin': True,
                }
            }
        ]
        )
        self._method_arns.append(
            GDPcg_post_method.method_arn
        )
        # cors
        self.add_cors_options(entity_GDPcg)

        # resource result
        entity_result = self._api.root.add_resource("result")
        entity_result_integration = apigw.LambdaIntegration(
            TargetLambda.get_lambda_functions('result'),
            proxy=False,
            integration_responses=[
            {
                'statusCode': '200',
                'responseParameters': {
                'method.response.header.Access-Control-Allow-Origin': "'*'",
                }
            }
                ],
        )

        entity_result_method = entity_result.add_method(
            "POST",
            entity_result_integration,
            authorization_type=apigw.AuthorizationType.IAM,
            method_responses=[{
                    'statusCode': '200',
                    'responseParameters': {
                        'method.response.header.Access-Control-Allow-Origin': True,
                    }
                }
            ]
        )
        self._method_arns.append(
            entity_result_method.method_arn
        )
        # cors
        self.add_cors_options(entity_result)

        # result/{id}
        # get submit result record information
        entity_result_info = entity_result.add_resource("{id}")
        get_result_info_intergration_options = apigw.IntegrationOptions(
            credentials_role=self.api_role,
            integration_responses=[
                {
                    'statusCode': '200',
                    'responseParameters':{
                        'method.response.header.Access-Control-Allow-Origin': "'*'"
                    },
                    'responseTemplates':{
                        'application/json':"{\"ID\": \"$input.path('$.Item.PK.S')\",\"Name\": \"$input.path('$.Item.Name.S')\",\"Timestamp\": \"$input.path('$.Item.Timestamp.S')\",\"Status\": \"$input.path('$.Item.Status.S')\",\"Result\": \"$input.path('$.Item.Result.S')\"}"
                    }
                }
            ],
            request_templates={
                'application/json': "{\"Key\":{\"PK\":{\"S\":\"$input.params('id')\"}},\"TableName\":\""+TargetDdb.get_dynamodb_tables("output").table_name+"\"}"
            }

        )
        get_result_info_intergration = apigw.AwsIntegration(
            service="dynamodb",
            action="GetItem",
            options=get_result_info_intergration_options
            )
        # method
        get_result_info_method = entity_result_info.add_method(
            'GET',
            get_result_info_intergration,
            authorization_type=apigw.AuthorizationType.IAM,
            method_responses=[{
                    'statusCode': '200',
                    'responseParameters': {
                        'method.response.header.Access-Control-Allow-Origin': True,
                }
            }
            ],
        )
        self._method_arns.append(
            get_result_info_method.method_arn
        )
        # cors
        self.add_cors_options(entity_result_info)

        # resource 
        # # check
        # entity_check = self._api.root.add_resource('check')
        # entity_check_integration = apigw.LambdaIntegration(
        #     TargetLambda.get_lambda_functions('check'),
        #     proxy=False,
        #     integration_responses=[
        #     {
        #         'statusCode': '200',
        #         'responseParameters': {
        #         'method.response.header.Access-Control-Allow-Origin': "'*'",
        #         }
        #     }
        #         ],
        # )

        # entity_check_method = entity_check.add_method(
        #     "POST",
        #     entity_check_integration,
        #     authorization_type=apigw.AuthorizationType.IAM,
        #     method_responses=[{
        #             'statusCode': '200',
        #             'responseParameters': {
        #                 'method.response.header.Access-Control-Allow-Origin': True,
        #             }
        #         }
        #     ]
        # )
        # self._method_arns.append(
        #     entity_check_method.method_arn
        # )
        # # cors
        # self.add_cors_options(entity_check)

    def get_method_arns(self):
        return self._method_arns
    ## add CORS to api
    def add_cors_options(self, apigw_resource):
        apigw_resource.add_method(
            'OPTIONS',
            apigw.MockIntegration(
                integration_responses=[
                    {
                        'statusCode': '200',
                        'responseParameters':{
                            'method.response.header.Access-Control-Allow-Headers':"'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'",
                            'method.response.header.Access-Control-Allow-Origin':"'*'",
                            'method.response.header.Access-Control-Allow-Methods': "'GET,POST,PUT,DELETE,OPTIONS'"
                        }
                    }
                ],
                passthrough_behavior=apigw.PassthroughBehavior.WHEN_NO_MATCH,
                request_templates={"application/json":"{\"statusCode\":200}"}
            ),
            method_responses=[
                {
                    'statusCode': '200',
                    'responseParameters':{
                        'method.response.header.Access-Control-Allow-Headers': True,
                        'method.response.header.Access-Control-Allow-Methods': True,
                        'method.response.header.Access-Control-Allow-Origin': True,
                    }
                }
            ]
        )


