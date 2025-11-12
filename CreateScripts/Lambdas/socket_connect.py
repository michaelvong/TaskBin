import json
import boto3
import datetime

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Lambda for $connect route.
    Stores the WebSocket connection in DynamoDB.

    Expected query parameters:
    - user_id
    - board_id
    """

    try:
        # WebSocket connection ID
        connection_id = event['requestContext']['connectionId']

        # Get query parameters (sent by client when connecting)
        query_params = event.get('queryStringParameters') or {}
        user_id = query_params.get('user_id')
        board_id = query_params.get('board_id')

        if not user_id or not board_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing user_id or board_id"})
            }

        # Current UTC time in ISO format
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

        # --- Store the connection (board-centric) ---
        connection_item = {
            "PK": f"BOARD#{board_id}",           # board-centric
            "SK": f"CONNECTION#{connection_id}", # unique per connection
            "Type": "connection",
            "board_id": board_id,
            "user_id": user_id,
            "connected_at": now_iso
        }

        table.put_item(Item=connection_item)

        return {"statusCode": 200, "body": "Connected successfully"}

    except Exception as e:
        print("Error in $connect Lambda:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
