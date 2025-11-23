import json
import boto3
import datetime

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Stores a WebSocket connection when a client connects.
    Expects query params:
      ?user_id=<email>&board_id=<uuid>
    """

    try:
        connection_id = event["requestContext"]["connectionId"]
        params = event.get("queryStringParameters") or {}

        user_id = params.get("user_id")
        board_id = params.get("board_id")

        if not user_id or not board_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing user_id or board_id"})
            }

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        table.put_item(
            Item={
                "PK": f"BOARD#{board_id}",
                "SK": f"CONNECTION#{connection_id}",
                "type": "connection",
                "board_id": board_id,
                "user_id": user_id,
                "connected_at": now
            }
        )

        return {"statusCode": 200, "body": "Connected"}

    except Exception as e:
        print("❌ Connect error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
