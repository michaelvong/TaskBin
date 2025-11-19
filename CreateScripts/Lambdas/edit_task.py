import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to edit a task's metadata.
    Input JSON:
    {
        "user_id": "<uuid>",      # who is editing the task (must be a member)
        "board_id": "<board-uuid>",
        "task_id": "<task-uuid>",
        "title": "<optional new title>",
        "description": "<optional new description>",
        "finish_by": "<optional new ISO timestamp>",
        "status": "<optional new status>",
        "assigned_to": "<optional new assigned user_id or null to unassign>"
    }

    Updates:
    - Board-centric task row (BOARD#board_id / TASK#task_id)
    - Task metadata row (TASK#task_id / METADATA)
    - User-centric task row(s) if assigned_to changes
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
            return {"statusCode": 400, "body": json.dumps({"error": "Missing required fields: user_id, board_id, task_id"})}

        board_sk = f"BOARD#{board_id}"
        task_sk = f"TASK#{task_id}"

        # ---------------------------------
        # Verify user is a member of the board
        # ---------------------------------
        user_board_resp = table.get_item(Key={"PK": f"USER#{user_id}", "SK": board_sk})
        if "Item" not in user_board_resp:
            return {"statusCode": 403, "body": json.dumps({"error": "User is not a member of this board"})}

        # ---------------------------------
        # Get existing board-centric task row
        # ---------------------------------
        board_task_resp = table.get_item(Key={"PK": board_sk, "SK": task_sk})
        board_task_item = board_task_resp.get("Item")
        if not board_task_item:
            return {"statusCode": 404, "body": json.dumps({"error": "Task not found"})}

        old_assigned_to = board_task_item.get("assigned_to")

        # ---------------------------------
        # Get updates from request
        # ---------------------------------
        title = body.get("title")
        description = body.get("description")
        finish_by = body.get("finish_by")
        status = body.get("status")
        assigned_to = body.get("assigned_to")  # can be None to unassign

        update_expr = []
        expr_values = {}

        # Build update expressions for board-centric task
        if title is not None:
            update_expr.append("title = :title")
            expr_values[":title"] = title
        if description is not None:
            update_expr.append("description = :desc")
            expr_values[":desc"] = description
        if finish_by is not None:
            update_expr.append("finish_by = :fb")
            expr_values[":fb"] = finish_by
        if status is not None:
            update_expr.append("status = :status")
            expr_values[":status"] = status
        # Always update assigned_to if provided (including None)
        if "assigned_to" in body:
            update_expr.append("assigned_to = :assigned")
            expr_values[":assigned"] = assigned_to

        if update_expr:
            table.update_item(
                Key={"PK": board_sk, "SK": task_sk},
                UpdateExpression="SET " + ", ".join(update_expr),
                ExpressionAttributeValues=expr_values
            )

            table.update_item(
                Key={"PK": f"TASK#{task_id}", "SK": "METADATA"},
                UpdateExpression="SET " + ", ".join(update_expr),
                ExpressionAttributeValues=expr_values
            )

        # ---------------------------------
        # Update user-centric row if assigned_to changed
        # ---------------------------------
        # Remove old user assignment if it existed and changed
        if old_assigned_to and old_assigned_to != assigned_to:
            table.delete_item(Key={"PK": f"USER#{old_assigned_to}", "SK": task_sk})

        # Add new user assignment if assigned_to is provided
        if assigned_to and assigned_to != old_assigned_to:
            user_task_item = {
                "PK": f"USER#{assigned_to}",
                "SK": task_sk,
                "task_id": task_id,
                "board_id": board_id,
                "title": title or board_task_item.get("title"),
                "description": description or board_task_item.get("description"),
                "created_at": board_task_item.get("created_at"),
                "finish_by": finish_by or board_task_item.get("finish_by"),
                "created_by": board_task_item.get("created_by"),
                "status": status or board_task_item.get("status"),
                "type": "user_task"
            }
            table.put_item(Item=user_task_item)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Task {task_id} updated successfully",
                "task_id": task_id,
                "board_id": board_id
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
