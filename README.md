# Amazon Connect Caller Routing

## Overview

This project implements an inbound caller-routing workflow using Amazon Connect, AWS Lambda, DynamoDB, and AWS CDK.

When a caller dials the Amazon Connect number, the contact flow captures the caller’s phone number and sends it to a Lambda lookup function. The function checks DynamoDB and returns one of three customer types:

- `VIP`
- `KNOWN`
- `UNKNOWN`

Amazon Connect then routes the caller based on that customer type. Before the call disconnects, a second Lambda function logs the call outcome to DynamoDB.

---

## Architecture

```text
Caller
  -> Amazon Connect Phone Number
  -> InboundCallerRoutingFlow
  -> Customer Lookup Lambda
  -> DynamoDB Customers Table
  -> Route by customerType
      -> VIP path
      -> Known path
      -> Unknown/Fallback path
  -> Call Logger Lambda
  -> DynamoDB Call Logs Table
  -> Disconnect
```

### AWS Services

- Amazon Connect
- AWS Lambda
- Amazon DynamoDB
- AWS CDK
- AWS IAM / CloudFormation

---

## Project Structure

```text
amazon-connect-caller-routing/
  README.md
  app.py
  cdk.json
  requirements.txt
  connect_caller_routing/
    stack.py
  lambda/
    customer_lookup/
      app.py
    call_logger/
      app.py
  scripts/
    seed_customer.py
```

---

## Data Model

### Customers Table

Table name:

```text
connect-caller-routing-customers
```

Partition key:

```text
phoneNumber
```

Example item:

```json
{
  "phoneNumber": "+16305202420",
  "customerType": "VIP",
  "customerName": "Amritpal Rajput",
  "accountNumber": "100001"
}
```

### Call Logs Table

Table name:

```text
connect-caller-routing-call-logs
```

Partition key:

```text
contactId
```

Example item:

```json
{
  "contactId": "test-contact-001",
  "phoneNumber": "+16305202420",
  "customerType": "VIP",
  "route": "VIP",
  "lookupStatus": "SUCCESS",
  "accountNumberEntered": "",
  "timestamp": "2026-05-04T18:49:20.353455+00:00"
}
```

---

## Deployment Instructions

### Prerequisites

Install:

- Python 3.12+
- Node.js LTS
- AWS CLI
- AWS CDK CLI

Install CDK:

```powershell
npm install -g aws-cdk
```

Configure AWS credentials:

```powershell
aws configure
aws sts get-caller-identity
```

### Deploy

From the project root:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cdk synth
cdk bootstrap
cdk deploy
```

Approve IAM changes when prompted.

Expected CDK outputs:

```text
CustomersTableName = connect-caller-routing-customers
CallLogsTableName = connect-caller-routing-call-logs
CustomerLookupFunctionName = connect-caller-routing-customer-lookup
CallLoggerFunctionName = connect-caller-routing-call-logger
```

---

## Seed Test Data

Update `scripts/seed_customer.py` with the phone number you will test from. Use E.164 format:

```text
+16305202420
```

Run:

```powershell
python scripts/seed_customer.py
```

This creates sample VIP and Known customer records in DynamoDB.

---

## Lambda Testing

### Test Customer Lookup

Create a test payload:

```powershell
$json = @'
{
  "Details": {
    "ContactData": {
      "CustomerEndpoint": {
        "Address": "+16305202420"
      }
    }
  }
}
'@

[System.IO.File]::WriteAllText("lookup-vip-payload.json", $json, [System.Text.UTF8Encoding]::new($false))
```

Invoke the lookup Lambda:

```powershell
aws lambda invoke `
  --function-name connect-caller-routing-customer-lookup `
  --cli-binary-format raw-in-base64-out `
  --payload file://lookup-vip-payload.json `
  response.json
```

Expected result:

```json
{
  "lookupStatus": "SUCCESS",
  "customerType": "VIP",
  "customerName": "Amritpal Rajput",
  "phoneNumber": "+16305202420",
  "accountNumber": "100001"
}
```

### Test Call Logger

```powershell
$json = @'
{
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
'@

[System.IO.File]::WriteAllText("logger-payload.json", $json, [System.Text.UTF8Encoding]::new($false))
```

```powershell
aws lambda invoke `
  --function-name connect-caller-routing-call-logger `
  --cli-binary-format raw-in-base64-out `
  --payload file://logger-payload.json `
  logger-response.json
```

Verify the log:

```powershell
aws dynamodb scan `
  --table-name connect-caller-routing-call-logs
```

---

## Amazon Connect Setup

After CDK deployment:

1. Open the Amazon Connect instance in the same AWS region.
2. Go to **Flows**.
3. Associate these Lambda functions with the instance:
   - `connect-caller-routing-customer-lookup`
   - `connect-caller-routing-call-logger`
4. Create and publish a contact flow named:

```text
InboundCallerRoutingFlow
```

The flow should:

1. Play an initial greeting.
2. Invoke the customer lookup Lambda.
3. Save Lambda response values as contact attributes:
   - `customerType`
   - `customerName`
   - `lookupStatus`
   - `phoneNumber`
4. Check `customerType`.
5. Route to VIP, Known, Unknown, or Fallback path.
6. Invoke the call logger Lambda.
7. Play a final message and disconnect.

Once the Amazon Connect phone number quota is approved:

1. Claim a phone number.
2. Associate the number with `InboundCallerRoutingFlow`.
3. Place a test call.

---

## Contact Flow Behavior

### VIP

- Plays personalized VIP greeting.
- Sets `route = VIP`.
- Logs the call.
- Plays simulated VIP support prompt.
- Disconnects.

### Known

- Plays personalized standard greeting.
- Sets `route = STANDARD`.
- Logs the call.
- Plays simulated standard support prompt.
- Disconnects.

### Unknown

- Prompts caller to continue with account lookup.
- Uses DTMF option `1` for the demo path.
- Sets `route = FALLBACK`.
- Logs the call.
- Plays fallback support prompt.
- Disconnects.

---

## Current Demo Status

Completed:

- CDK infrastructure deployed
- DynamoDB tables created
- Lookup Lambda deployed and tested
- Logger Lambda deployed and tested
- Amazon Connect contact flow created and published
- Lambda functions associated with Amazon Connect

Pending:

- Claiming an Amazon Connect phone number
- Associating the phone number with the published flow
- Final live inbound call test

Reason:

An Amazon Connect service quota increase is currently pending. Once approved, the phone number will be claimed and the final call test will be completed.

---

## Assumptions and Tradeoffs

- Phone numbers are stored in E.164 format.
- VIP, Known, and Fallback routing are simulated with prompts instead of real agent queues.
- The contact flow was configured manually in Amazon Connect, while backend infrastructure is managed by CDK.
- DynamoDB tables use `RemovalPolicy.DESTROY` because this is a demo project.
- Lookup or attribute errors route to fallback instead of disconnecting abruptly.

---

## Known Limitations

- Live call test is pending until Amazon Connect quota approval.
- No real queues, agents, routing profiles, or hours of operation are configured.
- No frontend dashboard for call logs.
- No production monitoring or alarms.
- Contact flow is not fully managed through IaC.

---

## Cleanup

To remove CDK-managed resources:

```powershell
cdk destroy
```

Manual Amazon Connect resources, such as flows and phone numbers, should be cleaned up separately in the Amazon Connect console.
