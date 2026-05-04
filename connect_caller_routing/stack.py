from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_iam as iam,
)
from constructs import Construct


class ConnectCallerRoutingStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        customers_table = dynamodb.Table(
            self,
            "CustomersTable",
            table_name="connect-caller-routing-customers",
            partition_key=dynamodb.Attribute(
                name="phoneNumber",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        call_logs_table = dynamodb.Table(
            self,
            "CallLogsTable",
            table_name="connect-caller-routing-call-logs",
            partition_key=dynamodb.Attribute(
                name="contactId",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        lookup_function = lambda_.Function(
            self,
            "CustomerLookupFunction",
            function_name="connect-caller-routing-customer-lookup",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("lambda/customer_lookup"),
            timeout=Duration.seconds(8),
            environment={
                "CUSTOMERS_TABLE_NAME": customers_table.table_name
            }
        )

        logger_function = lambda_.Function(
            self,
            "CallLoggerFunction",
            function_name="connect-caller-routing-call-logger",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.lambda_handler",
            code=lambda_.Code.from_asset("lambda/call_logger"),
            timeout=Duration.seconds(8),
            environment={
                "CALL_LOGS_TABLE_NAME": call_logs_table.table_name
            }
        )

        customers_table.grant_read_data(lookup_function)
        call_logs_table.grant_write_data(logger_function)

        lookup_function.add_permission(
            "AllowAmazonConnectInvokeLookup",
            principal=iam.ServicePrincipal("connect.amazonaws.com"),
            action="lambda:InvokeFunction"
        )

        logger_function.add_permission(
            "AllowAmazonConnectInvokeLogger",
            principal=iam.ServicePrincipal("connect.amazonaws.com"),
            action="lambda:InvokeFunction"
        )

        CfnOutput(
            self,
            "CustomersTableName",
            value=customers_table.table_name
        )

        CfnOutput(
            self,
            "CallLogsTableName",
            value=call_logs_table.table_name
        )

        CfnOutput(
            self,
            "CustomerLookupFunctionName",
            value=lookup_function.function_name
        )

        CfnOutput(
            self,
            "CallLoggerFunctionName",
            value=logger_function.function_name
        )