import os
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(os.environ["CALL_LOGS_TABLE_NAME"])


def lambda_handler(event, context):
    print("Received event:", event)

    try:
        contact_data = event.get("Details", {}).get("ContactData", {})
        attributes = contact_data.get("Attributes", {})

        contact_id = contact_data.get("ContactId")

        phone_number = (
            contact_data.get("CustomerEndpoint", {})
                        .get("Address")
        )

        customer_type = attributes.get("customerType", "UNKNOWN")
        route = attributes.get("route", "FALLBACK")
        lookup_status = attributes.get("lookupStatus", "UNKNOWN")
        account_number_entered = attributes.get("accountNumberEntered", "")

        if not contact_id:
            contact_id = f"missing-contact-id-{datetime.now(timezone.utc).isoformat()}"

        item = {
            "contactId": contact_id,
            "phoneNumber": phone_number or "UNKNOWN",
            "customerType": customer_type,
            "route": route,
            "lookupStatus": lookup_status,
            "accountNumberEntered": account_number_entered,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        table.put_item(Item=item)

        return {
            "logStatus": "SUCCESS",
            "contactId": contact_id
        }

    except ClientError as error:
        print("DynamoDB logging error:", error)

        return {
            "logStatus": "ERROR",
            "errorMessage": "Failed to write call log"
        }

    except Exception as error:
        print("Unexpected logging error:", error)

        return {
            "logStatus": "ERROR",
            "errorMessage": "Unexpected call logging failure"
        }