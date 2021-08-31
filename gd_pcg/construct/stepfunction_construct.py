import os
import json

from aws_cdk import (
    core,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as sfn_tasks,
    aws_iam as iam,
    )

class SfnConstruct(core.Construct):

    def __init__(self,scope:core.Construct,id:str,TargetLambda = "default",TargetBatch = "default",TargetS3="default",**kwargs):
        super().__init__(scope, id, **kwargs)

        self.step_functions = {}

        #############################################
        # statemachine
        #############################################
        # 1.fisrt step
        first_task = sfn.Task(
            self,
            "startat-dynamodb-putitem",
            task=sfn_tasks.InvokeFunction(
                TargetLambda.get_lambda_functions("startat_dynamodb_putitem")
            ),
            parameters={
                "ID.$": "$.ID",
                "Timestamp.$": "$.Timestamp",
                "s3_sequence_file.$": "$.s3_sequence_file"
            },
            result_path="$.Paras"
        )

        # 2. GDPcg step
        GDPcg_task = sfn.Task(
            self,
            "run GDPcg",
            task=sfn_tasks.InvokeFunction(
                TargetLambda.get_lambda_functions("GDPcg")
            ),
            parameters={
                "ID.$": "$.ID",
                "database.$": "$.database",
                "user_upload_database.$": "$.user_upload_database",
                "s3_sequence_file.$": "$.s3_sequence_file",
                "s3_plasmid_file.$": "$.s3_plasmid_file",
                "max_left_arm_seq_length.$": "$.max_left_arm_seq_length",
                "min_left_arm_seq_length.$": "$.min_left_arm_seq_length",
                "max_right_arm_seq_length.$": "$.max_right_arm_seq_length",
                "min_right_arm_seq_length.$": "$.min_right_arm_seq_length",
                "max_verify_1_up_ponit.$": "$.max_verify_1_up_ponit",
                "min_verify_1_up_ponit.$": "$.min_verify_1_up_ponit",
                "max_verify_1_down_ponit.$": "$.max_verify_1_down_ponit",
                "min_verify_1_down_ponit.$": "$.min_verify_1_down_ponit",
                "max_verify_2_down_ponit.$": "$.max_verify_2_down_ponit",
                "min_verify_2_down_ponit.$": "$.min_verify_2_down_ponit",
                "left_arm_primer_opt_tm.$": "$.left_arm_primer_opt_tm",
                "left_arm_primer_min_tm.$": "$.left_arm_primer_min_tm",
                "left_arm_primer_max_tm.$": "$.left_arm_primer_max_tm",
                "left_arm_primer_min_gc.$": "$.left_arm_primer_min_gc",
                "left_arm_primer_max_gc.$": "$.left_arm_primer_max_gc",
                "right_arm_primer_opt_tm.$": "$.right_arm_primer_opt_tm",
                "right_arm_primer_min_tm.$": "$.right_arm_primer_min_tm",
                "right_arm_primer_max_tm.$": "$.right_arm_primer_max_tm",
                "right_arm_primer_min_gc.$": "$.right_arm_primer_min_gc",
                "right_arm_primer_max_gc.$": "$.right_arm_primer_max_gc",
                "verify_1_primer_opt_tm.$": "$.verify_1_primer_opt_tm",
                "verify_1_primer_min_tm.$": "$.verify_1_primer_min_tm",
                "verify_1_primer_max_tm.$": "$.verify_1_primer_max_tm",
                "verify_1_primer_min_tm.$": "$.verify_1_primer_min_tm",
                "verify_1_primer_min_gc.$": "$.verify_1_primer_min_gc",
                "verify_1_primer_max_gc.$": "$.verify_1_primer_max_gc",
                "verify_2_primer_opt_tm.$": "$.verify_2_primer_opt_tm",
                "verify_2_primer_min_tm.$": "$.verify_2_primer_min_tm",
                "verify_2_primer_max_tm.$": "$.verify_2_primer_max_tm",
                "verify_2_primer_min_gc.$": "$.verify_2_primer_min_gc",
                "verify_2_primer_max_gc.$": "$.verify_2_primer_max_gc"
            },
            result_path="$.Split"
        )

        # chain
        chain = sfn.Chain.start(first_task) \
                .next(GDPcg_task) \

        # statemachine
        statemachine = sfn.StateMachine(
            self,
            "GDPcg",
            definition=chain
        )
        
        self.step_functions["GDPcg"] = statemachine
    def get_step_functions(self,name):
        return self.step_functions[name]
