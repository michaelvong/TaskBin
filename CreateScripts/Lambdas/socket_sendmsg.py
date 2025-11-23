import os
import json
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

# ------------------------------------------------------------------
# WS_ENDPOINT is now injected by BuildMain during deployment
# Example: "https://abc123.execute-api.us-west-1.amazonaws.com/prod"
# ------------------------------------------------------------------
WS_ENDPOINT = os.environ.get("WS_ENDPOINT")

if not WS_ENDPOINT:
    raise ValueError("Missing WS_ENDPOINT environment variable.")

# Build API Gateway Management API client dynamically
apigateway = boto3.client(
    "apigatewaymanagementapi",
    endpoint_url=WS_ENDPOINT
)


def lambda_handler(event, context):
    """
    Broadcasts a message to all connections for a board.

    Expected event (from WebSocket):
        {
            "action": "taskUpdated",
            "board_id": "...",
            "user_id": "...",
            "payload": {...}   # optional details
        }
    """

    print("🔍 Incoming WebSocket event:", event)

    # ---------------------------
    # Parse body correctly
    # ---------------------------
    try:
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)
        elif not body:
            body = event  # allow direct testing
    except Exception:
        return {"statusCode": 400, "body": "Invalid JSON body"}

    action = body.get("action") or "message"
    board_id = body.get("board_id")
    user_id = body.get("user_id")
    payload = body.get("payload", {})

    if not board_id or not user_id:
        return {"statusCode": 400, "body": "Missing board_id or user_id"}

    # ---------------------------
    # Query all WebSocket connections for this board
    # ---------------------------
    try:
        resp = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": f"BOARD#{board_id}",
                ":sk": "CONNECTION#"
            }
        )
        connections = resp.get("Items", [])

    except Exception as e:
        print("❌ DynamoDB query error:", e)
        return {"statusCode": 500, "body": "DynamoDB query failed"}

    # ---------------------------
    # Prepare payload to broadcast
    # ---------------------------
    message_to_send = {
        "action": action,
        "board_id": board_id,
        "from": user_id,
        "payload": payload
    }

    # ---------------------------
    # Send message to each live connection
    # ---------------------------
    disconnected = 0
    sent = 0

    for conn in connections:
        connection_id = conn["SK"].split("#")[1]

        try:
            apigateway.post_to_connection(
                Data=json.dumps(message_to_send),
                ConnectionId=connection_id
            )
            sent += 1

        except apigateway.exceptions.GoneException:
            # Stale connection — remove it
            table.delete_item(Key={"PK": conn["PK"], "SK": conn["SK"]})
            disconnected += 1

        except Exception as e:
            print(f"❌ Error sending to {connection_id}:", e)

    print(f"📡 Broadcast complete → sent={sent}, removed stale={disconnected}")

    return {"statusCode": 200, "body": "Message broadcasted"}
