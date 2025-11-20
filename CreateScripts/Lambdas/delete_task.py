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
    Path: DELETE /boards/{board_id}/tasks/{task_id}

    Body JSON:
    {
        "user_id": "<uuid>"   # who is requesting deletion
    }

    Deletes:
    - Board-centric task row (BOARD#board_id / TASK#task_id)
    - Task metadata row (TASK#task_id / METADATA)
    - User-centric task row (USER#user_id / TASK#task_id), if assigned
    """

    try:
        # ---------------------------------
        # Parse path parameters
        # ---------------------------------
        path_params = event.get("pathParameters", {})
        board_id = path_params.get("board_id")
        task_id = path_params.get("task_id")

        if not board_id or not task_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required path parameters: board_id, task_id"})
            }

        # ---------------------------------
        # Parse request body for user_id
        # ---------------------------------
        if "body" in event and event["body"]:
            body = json.loads(event["body"])
        else:
            body = {}

        user_id = body.get("user_id")
        if not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required field in body: user_id"})
            }

        board_sk = f"BOARD#{board_id}"
        task_sk = f"TASK#{task_id}"

        # ---------------------------------
        # Verify board exists
        # ---------------------------------
        board_lookup = table.scan(
            FilterExpression="SK = :sk AND begins_with(PK, :prefix)",
            ExpressionAttributeValues={
                ":sk": board_sk,
                ":prefix": "USER#"
            }
        ).get("Items", [])

        if not board_lookup:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Board not found"})
            }

        # ---------------------------------
        # Verify user is a member or owner of the board
        # ---------------------------------
        user_board_item = table.get_item(
            Key={"PK": f"USER#{user_id}", "SK": board_sk}
        ).get("Item")

        if not user_board_item:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "User is not authorized to delete tasks on this board"})
            }

        # ---------------------------------
        # Get board-centric task row
        # ---------------------------------
        board_task_resp = table.get_item(Key={"PK": board_sk, "SK": task_sk})
        board_task_item = board_task_resp.get("Item")

        if not board_task_item:
            return {"statusCode": 404, "body": json.dumps({"error": "Task not found"})}

        assigned_to = board_task_item.get("assigned_to")

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
