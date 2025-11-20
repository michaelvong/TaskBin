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
        # Parse path parameters (task_id only)
        # ---------------------------------
        path_params = event.get("pathParameters", {}) or {}
        task_id = path_params.get("task_id")

        if not task_id:
            return {"statusCode": 400,
                    "body": json.dumps({"error": "Missing required path parameter: task_id"})}

        task_sk = f"TASK#{task_id}"

        # ---------------------------------
        # Parse body (only user_id + optional fields)
        # ---------------------------------
        body = json.loads(event.get("body", "{}"))

        user_id = body.get("user_id")
        if not user_id:
            return {"statusCode": 400,
                    "body": json.dumps({"error": "Missing required field: user_id"})}

        # ---------------------------------
        # Fetch metadata: TASK#task_id / METADATA
        # ---------------------------------
        metadata_resp = table.get_item(
            Key={"PK": f"TASK#{task_id}", "SK": "METADATA"}
        )
        metadata_item = metadata_resp.get("Item")

        if not metadata_item:
            return {"statusCode": 404,
                    "body": json.dumps({"error": "Task metadata not found"})}

        # Extract board_id from metadata
        board_id = metadata_item.get("board_id")
        board_pk = f"BOARD#{board_id}"

        # ---------------------------------
        # Verify user is a member of this board
        # ---------------------------------
        membership = table.get_item(
            Key={"PK": f"USER#{user_id}", "SK": board_pk}
        ).get("Item")

        if not membership:
            return {"statusCode": 403,
                    "body": json.dumps({"error": "User is not a member of this board"})}

        # ---------------------------------
        # Fetch board-centric task row
        # ---------------------------------
        board_task_resp = table.get_item(
            Key={"PK": board_pk, "SK": task_sk}
        )
        board_task_item = board_task_resp.get("Item")

        if not board_task_item:
            return {"statusCode": 404,
                    "body": json.dumps({"error": "Task not found on board"})}

        old_assigned_to = board_task_item.get("assigned_to")

        # ---------------------------------
        # Collect editable fields
        # ---------------------------------
        title = body.get("title")
        description = body.get("description")
        finish_by = body.get("finish_by")
        status = body.get("status")
        assigned_to = body.get("assigned_to") if "assigned_to" in body else None

        update_expr = []
        expr_values = {}

        if title is not None:
            update_expr.append("title = :t")
            expr_values[":t"] = title

        if description is not None:
            update_expr.append("description = :d")
            expr_values[":d"] = description

        if finish_by is not None:
            update_expr.append("finish_by = :fb")
            expr_values[":fb"] = finish_by

        if status is not None:
            update_expr.append("status = :s")
            expr_values[":s"] = status

        if "assigned_to" in body:  # allow None to unassign
            update_expr.append("assigned_to = :a")
            expr_values[":a"] = assigned_to

        # ---------------------------------
        # Apply updates to board-centric and metadata rows
        # ---------------------------------
        if update_expr:
            update_str = "SET " + ", ".join(update_expr)

            table.update_item(
                Key={"PK": board_pk, "SK": task_sk},
                UpdateExpression=update_str,
                ExpressionAttributeValues=expr_values
            )

            table.update_item(
                Key={"PK": f"TASK#{task_id}", "SK": "METADATA"},
                UpdateExpression=update_str,
                ExpressionAttributeValues=expr_values
            )

        # ---------------------------------
        # Handle user-centric reassignment
        # ---------------------------------

        # Remove old user-task if changed
        if old_assigned_to and old_assigned_to != assigned_to:
            table.delete_item(
                Key={"PK": f"USER#{old_assigned_to}", "SK": task_sk}
            )

        # Add new user-task
        if assigned_to and assigned_to != old_assigned_to:
            table.put_item(
                Item={
                    "PK": f"USER#{assigned_to}",
                    "SK": task_sk,
                    "task_id": task_id,
                    "board_id": board_id,
                    "title": title or board_task_item["title"],
                    "description": description or board_task_item["description"],
                    "created_at": board_task_item["created_at"],
                    "finish_by": finish_by or board_task_item["finish_by"],
                    "created_by": board_task_item["created_by"],
                    "status": status or board_task_item["status"],
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
        return {"statusCode": 500,
                "body": json.dumps({"error": str(e)})}
