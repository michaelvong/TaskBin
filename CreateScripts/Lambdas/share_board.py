import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Share a board with another user.

    Input JSON:
    {
        "user_id": "<invoking-user-id>",       # must already be a member
        "board_id": "<board-uuid>",
        "share_with_user_id": "<target-user-id>",
        "role": "editor" | "viewer"            # optional, default = "editor"
    }

    Creates this item:

    PK = f"USER#{share_with_user_id}"
    SK = f"BOARD#{board_id}"
    role = "editor" or "viewer"
    joined_at = ISO timestamp
    type = "board_membership"
    """

    try:
        # ---------------------------------
        # Parse input
        # ---------------------------------
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        board_id = body.get("board_id")
        target_user_id = body.get("share_with_user_id")
        role = body.get("role", "editor")

        if not user_id or not board_id or not target_user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, board_id, share_with_user_id"})
            }

        board_sk = f"BOARD#{board_id}"

        # ---------------------------------
        # Verify invoking user is a member of the board
        # ---------------------------------
        resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": board_sk})
        if "Item" not in resp:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Invoking user is not a member of this board"})
            }

        # ---------------------------------
        # Insert membership row for the new user
        # ---------------------------------
        membership_item = {
            "PK": f"USER#{target_user_id}",
            "SK": board_sk,
            "user_id": target_user_id,
            "board_id": board_id,
            "role": role,
            "joined_at": datetime.now(timezone.utc).isoformat(),
            "type": "board_membership"
        }

        table.put_item(Item=membership_item)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"User {target_user_id} added to board {board_id}",
                "board_id": board_id,
                "added_user_id": target_user_id,
                "role": role
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
