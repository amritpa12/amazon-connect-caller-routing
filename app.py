#!/usr/bin/env python3

import aws_cdk as cdk

from connect_caller_routing.stack import ConnectCallerRoutingStack


app = cdk.App()

ConnectCallerRoutingStack(
    app,
    "ConnectCallerRoutingStack"
)

app.synth()