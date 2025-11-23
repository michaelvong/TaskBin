import json
import boto3

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Removes the WebSocket connection from DynamoDB on disconnect.
    """

    try:
        connection_id = event["requestContext"]["connectionId"]

        # Query to find board owning this connection
        resp = table.scan(
            FilterExpression="begins_with(SK, :sk)",
            ExpressionAttributeValues={":sk": f"CONNECTION#{connection_id}"}
        )

        items = resp.get("Items", [])

        # Remove each match
        for item in items:
            table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

        return {"statusCode": 200, "body": "Disconnected"}

    except Exception as e:
        print("❌ Disconnect error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
