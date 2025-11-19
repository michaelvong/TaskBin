import json
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Lightweight lambda to update only the status of a task.
    Input JSON:
    {
        "user_id": "<uuid>",
        "board_id": "<board-uuid>",
        "task_id": "<task-uuid>",
        "status": "<new-status>"
    }
    """

    try:
        # Parse input
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        board_id = body.get("board_id")
        task_id = body.get("task_id")
        new_status = body.get("status")

        if not user_id or not board_id or not task_id or not new_status:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields"})
            }

        board_sk = f"BOARD#{board_id}"
        task_sk = f"TASK#{task_id}"

        # --- Verify the user is a member of the board ---
        member_resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": board_sk})
        if "Item" not in member_resp:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "User is not a member of this board"})
            }

        # --- Update BOARD → TASK entry ---
        table.update_item(
            Key={"PK": f"BOARD#{board_id}", "SK": task_sk},
            UpdateExpression="SET #s = :new_status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":new_status": new_status}
        )

        # --- Update TASK → METADATA entry ---
        table.update_item(
            Key={"PK": f"TASK#{task_id}", "SK": "METADATA"},
            UpdateExpression="SET #s = :new_status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":new_status": new_status}
        )

        # --- Check if task is assigned to a user ---
        task_meta_resp = table.get_item(Key={"PK": f"TASK#{task_id}", "SK": "METADATA"})
        task_meta = task_meta_resp.get("Item", {})
        assigned_to = task_meta.get("assigned_to")

        # --- Update USER → TASK entry if it exists ---
        if assigned_to:
            table.update_item(
                Key={"PK": f"USER#{assigned_to}", "SK": task_sk},
                UpdateExpression="SET #s = :new_status",
                ExpressionAttributeNames={"#s": "status"},
                ExpressionAttributeValues={":new_status": new_status}
            )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Task status updated",
                "task_id": task_id,
                "new_status": new_status
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
