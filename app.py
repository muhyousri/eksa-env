#!/usr/bin/env python3
import os

import aws_cdk as cdk


from eksa_cdk_python.eksa_cdk_python_stack import EksaCdkPythonStack


app = cdk.App()
EksaCdkPythonStack(app, "EksaCdkPythonStack",
    )
app.synth()
