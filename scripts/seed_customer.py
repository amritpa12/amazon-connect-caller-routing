import boto3

TABLE_NAME = "connect-caller-routing-customers"

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


customers = [
    {
        "phoneNumber": "+16305202420",
        "customerType": "VIP",
        "customerName": "Amritpal Rajput",
        "accountNumber": "100001"
    },
    {
        "phoneNumber": "+15559876543",
        "customerType": "KNOWN",
        "customerName": "Marcus Lee",
        "accountNumber": "100002"
    }
]


for customer in customers:
    table.put_item(Item=customer)
    print(f"Inserted customer: {customer['phoneNumber']} as {customer['customerType']}")


print("Seed data inserted successfully.")