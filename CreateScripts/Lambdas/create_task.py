import json
import boto3
import uuid
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to create a new task in a board.
    Path: POST /boards/{board_id}/tasks
    """

    try:
        # ---------------------------------
        # Parse path parameter: board_id
        # ---------------------------------
        board_id = event.get("pathParameters", {}).get("board_id")
        if not board_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing board_id in URL path"})
            }

        # ---------------------------------
        # Parse request body
        # ---------------------------------
        if "body" in event and event["body"]:
            body = json.loads(event["body"])
        else:
            body = {}

        user_id = body.get("user_id")
        title = body.get("title")
        description = body.get("description", "")
        finish_by = body.get("finish_by")
        assigned_to = body.get("assigned_to")
        task_status = body.get("task_status", "todo")

        if not user_id or not title:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, title"})
            }

        # ---------------------------------
        # ✔️ NEW: Verify the user is a board owner or a member
        # ---------------------------------
        membership_item = table.get_item(
            Key={
                "PK": f"USER#{user_id}",
                "SK": f"BOARD#{board_id}"
            }
        ).get("Item")

        if not membership_item:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "User is not authorized (not a board member or owner)"})
            }

        # ---------------------------------
        # ✔️ Verify board exists (optional safety check)
        # ---------------------------------
        board_owner_lookup = table.scan(
            FilterExpression="SK = :sk AND begins_with(PK, :prefix)",
            ExpressionAttributeValues={
                ":sk": f"BOARD#{board_id}",
                ":prefix": "USER#"
            }
        ).get("Items", [])

        if not board_owner_lookup:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Board not found"})
            }

        # ---------------------------------
        # Generate unique task ID
        # ---------------------------------
        task_id = str(uuid.uuid4())
        created_at = datetime.now(timezone.utc).isoformat()

        # ---------------------------------
        # 1️⃣ Insert BOARD -> TASK entry
        # ---------------------------------
        board_task_item = {
            "PK": f"BOARD#{board_id}",
            "SK": f"TASK#{task_id}",
            "task_id": task_id,
            "board_id": board_id,
            "title": title,
            "description": description,
            "created_at": created_at,
            "finish_by": finish_by,
            "created_by": user_id,
            "task_status": task_status,
            "assigned_to": assigned_to,
            "type": "task"
        }
        table.put_item(Item=board_task_item)

        # ---------------------------------
        # 2️⃣ Insert TASK -> METADATA entry
        # ---------------------------------
        task_metadata_item = {
            "PK": f"TASK#{task_id}",
            "SK": "METADATA",
            "task_id": task_id,
            "board_id": board_id,
            "title": title,
            "description": description,
            "created_at": created_at,
            "finish_by": finish_by,
            "created_by": user_id,
            "task_status": task_status,
            "assigned_to": assigned_to,
            "type": "task_metadata"
        }
        table.put_item(Item=task_metadata_item)

        # ---------------------------------
        # 3️⃣ Insert USER -> TASK entry (if assigned)
        # ---------------------------------
        if assigned_to:
            user_task_item = {
                "PK": f"USER#{assigned_to}",
                "SK": f"TASK#{task_id}",
                "task_id": task_id,
                "board_id": board_id,
                "title": title,
                "description": description,
                "created_at": created_at,
                "finish_by": finish_by,
                "created_by": user_id,
                "task_status": task_status,
                "type": "user_task"
            }
            table.put_item(Item=user_task_item)

        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": "Task created successfully",
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
