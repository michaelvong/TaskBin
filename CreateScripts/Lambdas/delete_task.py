import json
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to delete a task.
    Input JSON:
    {
        "user_id": "<uuid>",   # who is requesting deletion
        "board_id": "<board-uuid>",
        "task_id": "<task-uuid>"
    }

    Deletes:
    - Board-centric task row (BOARD#board_id / TASK#task_id)
    - Task metadata row (TASK#task_id / METADATA)
    - User-centric task row (USER#user_id / TASK#task_id), if assigned
    """

    try:
        # ---------------------------------
        # Parse request body
        # ---------------------------------
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        board_id = body.get("board_id")
        task_id = body.get("task_id")

        if not user_id or not board_id or not task_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, board_id, task_id"})
            }

        board_sk = f"BOARD#{board_id}"
        task_sk = f"TASK#{task_id}"

        # ---------------------------------
        # Get board-centric task row
        # ---------------------------------
        board_task_resp = table.get_item(Key={"PK": board_sk, "SK": task_sk})
        board_task_item = board_task_resp.get("Item")

        if not board_task_item:
            return {"statusCode": 404, "body": json.dumps({"error": "Task not found"})}

        assigned_to = board_task_item.get("assigned_to")

        # ---------------------------------
        # Verify user is a member of the board
        # ---------------------------------
        user_board_resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": board_sk})
        if "Item" not in user_board_resp:
            return {"statusCode": 403, "body": json.dumps({"error": "User is not a member of this board"})}

        # ---------------------------------
        # Delete board-centric row
        # ---------------------------------
        table.delete_item(Key={"PK": board_sk, "SK": task_sk})

        # ---------------------------------
        # Delete task metadata row
        # ---------------------------------
        table.delete_item(Key={"PK": f"TASK#{task_id}", "SK": "METADATA"})

        # ---------------------------------
        # Delete user-centric row if assigned
        # ---------------------------------
        if assigned_to:
            table.delete_item(Key={"PK": f"USER#{assigned_to}", "SK": task_sk})

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Task {task_id} deleted successfully",
                "board_id": board_id,
                "task_id": task_id
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
