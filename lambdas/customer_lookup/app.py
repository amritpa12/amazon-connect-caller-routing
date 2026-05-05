import os
import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CUSTOMERS_TABLE_NAME"])


def lambda_handler(event, context):
    print("Received event:", event)

    try:
        phone_number = (
            event.get("Details", {})
                 .get("ContactData", {})
                 .get("CustomerEndpoint", {})
                 .get("Address")
        )

        if not phone_number:
            return {
                "lookupStatus": "INVALID_INPUT",
                "customerType": "UNKNOWN",
                "customerName": "",
                "phoneNumber": ""
            }

        response = table.get_item(
            Key={
                "phoneNumber": phone_number
            }
        )

        customer = response.get("Item")

        if not customer:
            return {
                "lookupStatus": "NOT_FOUND",
                "customerType": "UNKNOWN",
                "customerName": "",
                "phoneNumber": phone_number
            }

        return {
            "lookupStatus": "SUCCESS",
            "customerType": customer.get("customerType", "KNOWN"),
            "customerName": customer.get("customerName", ""),
            "phoneNumber": phone_number,
            "accountNumber": customer.get("accountNumber", "")
        }

    except ClientError as error:
        print("DynamoDB error:", error)

        return {
            "lookupStatus": "ERROR",
            "customerType": "UNKNOWN",
            "customerName": "",
            "phoneNumber": "",
            "errorMessage": "DynamoDB lookup failed"
        }

    except Exception as error:
        print("Unexpected error:", error)

        return {
            "lookupStatus": "ERROR",
            "customerType": "UNKNOWN",
            "customerName": "",
            "phoneNumber": "",
            "errorMessage": "Unexpected customer lookup failure"
        }