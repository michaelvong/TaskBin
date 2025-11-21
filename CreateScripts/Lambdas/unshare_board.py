import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Remove a user's membership from a board.

    Input JSON:
    {
        "user_id": "<invoking-user-id>",          # must be owner or editor (optional check)
        "board_id": "<board-uuid>",
        "remove_user_id": "<user-to-remove>"
    }

    Deletes:
    PK = USER#remove_user_id
    SK = BOARD#board_id
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
        remove_user_id = body.get("remove_user_id")

        if not user_id or not board_id or not remove_user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({
                    "error": "Missing required fields: user_id, board_id, remove_user_id"
                })
            }

        board_sk = f"BOARD#{board_id}"

        # ---------------------------------
        # Verify invoking user is a member of the board
        # ---------------------------------
        invoker_check = table.get_item(
            Key={"PK": f"USER#{user_id}", "SK": board_sk}
        )
        if "Item" not in invoker_check:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Invoking user is not a member of this board"})
            }

        # You *could* enforce owner-only removal here:
        # if invoker_check["Item"].get("role") != "owner":
        #     return {"statusCode": 403, "body": json.dumps({"error": "Only board owners can unshare"})}

        # ---------------------------------
        # Check membership for the user being removed
        # ---------------------------------
        membership_key = {"PK": f"USER#{remove_user_id}", "SK": board_sk}
        membership_check = table.get_item(Key=membership_key)

        if "Item" not in membership_check:
            return {
                "statusCode": 404,
                "body": json.dumps({
                    "error": f"User {remove_user_id} is not a member of board {board_id}"
                })
            }

        # ---------------------------------
        # Remove membership row
        # ---------------------------------
        table.delete_item(Key=membership_key)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"User {remove_user_id} removed from board {board_id}",
                "board_id": board_id,
                "removed_user_id": remove_user_id
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
