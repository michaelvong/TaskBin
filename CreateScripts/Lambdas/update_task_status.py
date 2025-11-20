import json
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to update only the status of a task.
    Input JSON:
    {
        "user_id": "<uuid>",
        "status": "<new-status>"
    }
    Route URL: /tasks/{task_id}/status
    """

    try:
        # -----------------------------
        # Grab task_id from route
        # -----------------------------
        path_params = event.get("pathParameters", {})
        task_id = path_params.get("task_id")
        if not task_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing task_id (in route)"})
            }

        # -----------------------------
        # Parse body
        # -----------------------------
        if "body" in event and event["body"]:
            body = json.loads(event["body"])
        else:
            body = {}

        user_id = body.get("user_id")
        new_status = body.get("status")

        if not user_id or not new_status:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id or status"})
            }

        task_sk = f"TASK#{task_id}"

        # -----------------------------
        # Check if task exists & get board_id
        # -----------------------------
        task_meta_resp = table.get_item(Key={"PK": task_sk, "SK": "METADATA"})
        task_meta = task_meta_resp.get("Item")
        if not task_meta:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Task not found"})
            }

        board_id = task_meta.get("board_id")
        if not board_id:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Corrupted task metadata: missing board_id"})
            }

        board_sk = f"BOARD#{board_id}"

        # -----------------------------
        # Verify the user is a member of the board
        # -----------------------------
        member_resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": board_sk})
        if "Item" not in member_resp:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "User is not a member of this board"})
            }

        # -----------------------------
        # Update BOARD → TASK entry
        # -----------------------------
        table.update_item(
            Key={"PK": board_sk, "SK": task_sk},
            UpdateExpression="SET #s = :new_status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":new_status": new_status}
        )

        # -----------------------------
        # Update TASK → METADATA entry
        # -----------------------------
        table.update_item(
            Key={"PK": task_sk, "SK": "METADATA"},
            UpdateExpression="SET #s = :new_status",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":new_status": new_status}
        )

        # -----------------------------
        # Update USER → TASK entry if assigned
        # -----------------------------
        assigned_to = task_meta.get("assigned_to")
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
                "board_id": board_id,
                "new_status": new_status
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
