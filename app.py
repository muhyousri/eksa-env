#!/usr/bin/env python3
import os

import aws_cdk as cdk


from eksa_cdk.eksa_cdk_stack import EksaCdkStack


app = cdk.App()
EksaCdkStack(app, "EksaCdkStack",
    )
app.synth()
