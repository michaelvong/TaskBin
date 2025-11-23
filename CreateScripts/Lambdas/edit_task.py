import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# --- DynamoDB ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    try:
        # ---------------------------------
        # Parse body (task_id + user_id + editable fields)
        # ---------------------------------
        body = json.loads(event.get("body", "{}"))

        task_id = body.get("task_id")
        user_id = body.get("user_id")

        if not task_id or not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: task_id, user_id"})
            }

        task_sk = f"TASK#{task_id}"

        # ---------------------------------
        # Fetch metadata: TASK#task_id / METADATA
        # ---------------------------------
        metadata_resp = table.get_item(
            Key={"PK": f"TASK#{task_id}", "SK": "METADATA"}
        )
        metadata_item = metadata_resp.get("Item")

        if not metadata_item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Task metadata not found"})
            }

        board_id = metadata_item.get("board_id")
        board_pk = f"BOARD#{board_id}"

        # ---------------------------------
        # Verify the user is part of the board
        # ---------------------------------
        membership = table.get_item(
            Key={"PK": f"USER#{user_id}", "SK": board_pk}
        ).get("Item")

        if not membership:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "User is not a member of this board"})
            }

        # ---------------------------------
        # Fetch board-centric task row
        # ---------------------------------
        board_task_resp = table.get_item(
            Key={"PK": board_pk, "SK": task_sk}
        )
        board_task_item = board_task_resp.get("Item")

        if not board_task_item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Task not found on board"})
            }

        old_assigned_to = board_task_item.get("assigned_to")

        # ---------------------------------
        # Collect editable fields
        # ---------------------------------
        editable_fields = {
            "title": body.get("title"),
            "description": body.get("description"),
            "finish_by": body.get("finish_by"),
            "task_status": body.get("task_status"),
        }

        # For assigned_to, allow null to unassign
        if "assigned_to" in body:
            editable_fields["assigned_to"] = body.get("assigned_to")

        update_expr = []
        expr_values = {}

        for key, val in editable_fields.items():
            if val is not None:
                update_expr.append(f"{key} = :{key}")
                expr_values[f":{key}"] = val

        # ---------------------------------
        # Apply updates to board + metadata rows
        # ---------------------------------
        if update_expr:
            update_str = "SET " + ", ".join(update_expr)

            # Update board task row
            table.update_item(
                Key={"PK": board_pk, "SK": task_sk},
                UpdateExpression=update_str,
                ExpressionAttributeValues=expr_values
            )

            # Update metadata row
            table.update_item(
                Key={"PK": f"TASK#{task_id}", "SK": "METADATA"},
                UpdateExpression=update_str,
                ExpressionAttributeValues=expr_values
            )

        # ---------------------------------
        # Handle reassignment
        # ---------------------------------
        assigned_to = body.get("assigned_to")

        # Remove old user-task link
        if old_assigned_to and old_assigned_to != assigned_to:
            table.delete_item(
                Key={"PK": f"USER#{old_assigned_to}", "SK": task_sk}
            )

        # Add new user-task link
        if assigned_to and assigned_to != old_assigned_to:
            table.put_item(
                Item={
                    "PK": f"USER#{assigned_to}",
                    "SK": task_sk,
                    "task_id": task_id,
                    "board_id": board_id,
                    "title": editable_fields.get("title") or board_task_item["title"],
                    "description": editable_fields.get("description") or board_task_item["description"],
                    "created_at": board_task_item["created_at"],
                    "finish_by": editable_fields.get("finish_by") or board_task_item["finish_by"],
                    "created_by": board_task_item["created_by"],
                    "task_status": editable_fields.get("task_status") or board_task_item["task_status"],
                    "type": "user_task"
                }
            )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Task {task_id} updated successfully",
                "task_id": task_id,
                "board_id": board_id
            })
        }

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
