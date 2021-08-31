#!/usr/bin/env python3
import os

from aws_cdk import core as cdk
from aws_cdk import core

from gd_pcg.stack.gd_pcg_stack import GdPcgStack

STACK_NAME = "GDPcg"
STAGE = "prod"


app = core.App()
GdPcgStack(
    app, 
    STACK_NAME +'-'+STAGE,
    Stage=STAGE
    )

app.synth()
