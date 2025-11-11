import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# --- DynamoDB single table name ---
TABLE_NAME = "TaskBin"

# --- Initialize DynamoDB resource ---
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Lambda to let a user join a board.
    Expects event to contain JSON body:
    {
        "user_id": "<user-uuid>",
        "board_id": "<board-uuid>"
    }

    Data model:
    - User-centric row: PK = USER#<user_id>, SK = BOARD#<board_id>
    - Board-centric membership row (optional): PK = BOARD#<board_id>, SK = USER#<user_id>
    """

    try:
        # --- Parse input body ---
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        board_id = body.get("board_id")

        if not user_id or not board_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, board_id"})
            }

        # --- Get board owner row ---
        owner_row = table.scan(
            FilterExpression="#T = :type_val AND SK = :sk_val",
            ExpressionAttributeNames={"#T": "Type"},  # alias for reserved keyword
            ExpressionAttributeValues={
                ":type_val": "board",
                ":sk_val": f"BOARD#{board_id}"
            },
            Limit=1
        ).get("Items", [])

        if not owner_row:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Board not found"})
            }

        owner_row = owner_row[0]
        owner_id = owner_row["owner_id"]

        # --- Check if user is already a member ---
        existing = table.get_item(
            Key={
                "PK": f"USER#{user_id}",
                "SK": f"BOARD#{board_id}"
            }
        ).get("Item")

        if existing:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "User is already a member of this board"})
            }

        # --- Prepare timestamps ---
        now_iso = datetime.now(timezone.utc).isoformat()

        # --- User-centric board row ---
        user_board_row = {
            "PK": f"USER#{user_id}",
            "SK": f"BOARD#{board_id}",
            "Type": "membership",
            "board_id": board_id,
            "owner_id": owner_id,
            "role": "member",
            "joined_at": now_iso
        }

        with table.batch_writer() as batch:
            batch.put_item(Item=user_board_row)

        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": f"User {user_id} joined board {board_id} successfully",
                "board_id": board_id,
                "user_id": user_id,
                "owner_id": owner_id
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
