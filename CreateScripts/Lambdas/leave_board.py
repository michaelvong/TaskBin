import json
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB single table name ---
TABLE_NAME = "TaskBin"

# --- Initialize DynamoDB resource ---
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Lambda to let a user leave a board.
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

        # --- Check if user is a member ---
        user_board_key = {"PK": f"USER#{user_id}", "SK": f"BOARD#{board_id}"}
        response = table.get_item(Key=user_board_key)
        item = response.get("Item")

        if not item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "User is not a member of this board"})
            }

        # --- Prevent owner from leaving (optional) ---
        if item.get("role") == "owner":
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Owner cannot leave the board"})
            }

        # --- Delete both user-centric and board-centric rows ---
        board_member_key = {"PK": f"BOARD#{board_id}", "SK": f"USER#{user_id}"}

        with table.batch_writer() as batch:
            batch.delete_item(Key=user_board_key)
            batch.delete_item(Key=board_member_key)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"User {user_id} left board {board_id} successfully",
                "board_id": board_id,
                "user_id": user_id
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
