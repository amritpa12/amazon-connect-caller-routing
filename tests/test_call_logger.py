import importlib
import os
from unittest.mock import MagicMock, patch


def load_logger_lambda(mock_table):
    with patch.dict(os.environ, {"CALL_LOGS_TABLE_NAME": "test-call-logs"}):
        with patch("boto3.resource") as mock_resource:
            mock_resource.return_value.Table.return_value = mock_table
            return importlib.import_module("lambdas.call_logger.app")


def test_call_logger_writes_vip_call_log():
    mock_table = MagicMock()
    app = load_logger_lambda(mock_table)

    event = {
        "Details": {
            "ContactData": {
                "ContactId": "test-contact-001",
                "CustomerEndpoint": {
                    "Address": "+16305202420"
                },
                "Attributes": {
                    "customerType": "VIP",
                    "route": "VIP",
                    "lookupStatus": "SUCCESS",
                    "accountNumberEntered": ""
                }
            }
        }
    }

    result = app.lambda_handler(event, None)

    assert result["logStatus"] == "SUCCESS"
    assert result["contactId"] == "test-contact-001"

    mock_table.put_item.assert_called_once()
    written_item = mock_table.put_item.call_args.kwargs["Item"]

    assert written_item["contactId"] == "test-contact-001"
    assert written_item["phoneNumber"] == "+16305202420"
    assert written_item["customerType"] == "VIP"
    assert written_item["route"] == "VIP"
    assert written_item["lookupStatus"] == "SUCCESS"


def test_call_logger_defaults_unknown_values():
    mock_table = MagicMock()
    app = load_logger_lambda(mock_table)

    event = {
        "Details": {
            "ContactData": {
                "ContactId": "test-contact-002",
                "CustomerEndpoint": {
                    "Address": "+19999999999"
                },
                "Attributes": {}
            }
        }
    }

    result = app.lambda_handler(event, None)

    assert result["logStatus"] == "SUCCESS"

    written_item = mock_table.put_item.call_args.kwargs["Item"]

    assert written_item["customerType"] == "UNKNOWN"
    assert written_item["route"] == "FALLBACK"
    assert written_item["lookupStatus"] == "UNKNOWN"