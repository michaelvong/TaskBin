import json
import boto3
import uuid
from botocore.exceptions import ClientError
from datetime import datetime, timezone

# --- DynamoDB single table name ---
TABLE_NAME = "TaskBin"

# --- Initialize DynamoDB resource ---
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Lambda to create a new board and associate it with a user.
    Expects event to contain JSON body:
    {
        "user_id": "<user-uuid>",
        "board_name": "<string>",
        "description": "<optional string>"
    }

    Data model (single table):
    PK = "USER#<user_id>"
    SK = "BOARD#<board_id>"
    Type = "board"
    """

    try:
        # Parse input body (handle API Gateway or direct invocation)
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event
        user_id = body.get("user_id")
        board_name = body.get("board_name")
        description = body.get("description", "")

        if not user_id or not board_name:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, board_name"})
            }

        # --- Generate a unique board ID ---
        board_id = str(uuid.uuid4())

        # --- Construct board item with owner_id and role ---
        board_item = {
            "PK": f"USER#{user_id}",
            "SK": f"BOARD#{board_id}",
            "Type": "board",
            "board_id": board_id,
            "user_id": user_id,        # optional, same as owner_id
            "owner_id": user_id,       # explicit owner
            "role": "owner",           # role for RBAC
            "board_name": board_name,
            "description": description,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        # --- Put the board item into the table ---
        table.put_item(Item=board_item)

        # --- Return success ---
        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": "Board created successfully",
                "board_id": board_id,
                "board_name": board_name
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

    except Exception as e:
        print("Error:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
