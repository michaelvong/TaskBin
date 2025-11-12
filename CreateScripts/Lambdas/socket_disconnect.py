import json
import boto3

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda for $disconnect route.
    Removes the connection from DynamoDB when a client disconnects.
    """
    try:
        connection_id = event['requestContext']['connectionId']

        # Query for the connection item (board-centric)
        # We need to scan since we may not know the board_id
        response = table.scan(
            FilterExpression="SK = :sk AND Type = :type",
            ExpressionAttributeValues={
                ":sk": f"CONNECTION#{connection_id}",
                ":type": "connection"
            },
            ProjectionExpression="PK, SK"
        )
        items = response.get("Items", [])

        # Delete the connection item(s)
        for item in items:
            table.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

        return {"statusCode": 200, "body": "Disconnected successfully"}

    except Exception as e:
        print("Error in $disconnect Lambda:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
