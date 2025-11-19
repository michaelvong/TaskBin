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
    Input JSON should contain:
    {
        "user_id": "<uuid>",           # who is creating the task
        "board_id": "<board-uuid>",
        "title": "<task title>",
        "description": "<optional description>",
        "finish_by": "<optional ISO timestamp>",
        "assigned_to": "<optional user_id>",
        "status": "<optional status, default 'todo'>"
    }
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
        title = body.get("title")
        description = body.get("description", "")
        finish_by = body.get("finish_by")  # optional ISO string
        assigned_to = body.get("assigned_to")  # optional user_id
        status = body.get("status", "todo")  # default to 'todo'

        if not user_id or not board_id or not title:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, board_id, title"})
            }

        # ---------------------------------
        # Verify board exists
        # ---------------------------------
        board_sk = f"BOARD#{board_id}"
        owner_query = table.scan(
            FilterExpression="SK = :sk AND begins_with(PK, :prefix)",
            ExpressionAttributeValues={
                ":sk": board_sk,
                ":prefix": "USER#"
            }
        ).get("Items", [])

        if not owner_query:
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
            "status": status,
            "assigned_to": assigned_to,  # always present (None if not assigned)
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
            "status": status,
            "assigned_to": assigned_to,  # optional
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
                "status": status,
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
