import importlib
import os
from unittest.mock import MagicMock, patch


def load_lookup_lambda(mock_table):
    with patch.dict(os.environ, {"CUSTOMERS_TABLE_NAME": "test-customers"}):
        with patch("boto3.resource") as mock_resource:
            mock_resource.return_value.Table.return_value = mock_table
            return importlib.import_module("lambdas.customer_lookup.app")


def test_customer_lookup_returns_vip_customer():
    mock_table = MagicMock()
    mock_table.get_item.return_value = {
        "Item": {
            "phoneNumber": "+16305202420",
            "customerType": "VIP",
            "customerName": "Amritpal Rajput",
            "accountNumber": "100001",
        }
    }

    app = load_lookup_lambda(mock_table)

    event = {
        "Details": {
            "ContactData": {
                "CustomerEndpoint": {
                    "Address": "+16305202420"
                }
            }
        }
    }

    result = app.lambda_handler(event, None)

    assert result["lookupStatus"] == "SUCCESS"
    assert result["customerType"] == "VIP"
    assert result["customerName"] == "Amritpal Rajput"
    assert result["accountNumber"] == "100001"


def test_customer_lookup_returns_unknown_when_not_found():
    mock_table = MagicMock()
    mock_table.get_item.return_value = {}

    app = load_lookup_lambda(mock_table)

    event = {
        "Details": {
            "ContactData": {
                "CustomerEndpoint": {
                    "Address": "+19999999999"
                }
            }
        }
    }

    result = app.lambda_handler(event, None)

    assert result["lookupStatus"] == "NOT_FOUND"
    assert result["customerType"] == "UNKNOWN"
    assert result["phoneNumber"] == "+19999999999"


def test_customer_lookup_handles_missing_phone_number():
    mock_table = MagicMock()

    app = load_lookup_lambda(mock_table)

    event = {
        "Details": {
            "ContactData": {}
        }
    }

    result = app.lambda_handler(event, None)

    assert result["lookupStatus"] == "INVALID_INPUT"
    assert result["customerType"] == "UNKNOWN"