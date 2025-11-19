import json
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to list tasks for a board.
    Input JSON:
    {
        "board_id": "<board-uuid>",
        "status": "<optional status filter>"
    }
    Returns:
    [
        {
            "task_id": "<task-uuid>",
            "title": "<task title>",
            "description": "<optional>",
            "created_at": "<ISO timestamp>",
            "finish_by": "<ISO timestamp, optional>",
            "created_by": "<user id>",
            "assigned_to": "<optional user id>",
            "status": "<task status>"
        },
        ...
    ]
    """
    try:
        # Parse input
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        board_id = body.get("board_id")
        status_filter = body.get("status")

        if not board_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing required field: board_id"})}

        board_pk = f"BOARD#{board_id}"
        sk_prefix = "TASK#"

        # Query all tasks for the board
        response = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": board_pk,
                ":sk": sk_prefix
            }
        )

        items = response.get("Items", [])

        # Optional filter by status
        if status_filter:
            items = [item for item in items if item.get("status") == status_filter]

        # Format output
        tasks = []
        for item in items:
            tasks.append({
                "task_id": item.get("task_id"),
                "title": item.get("title"),
                "description": item.get("description"),
                "created_at": item.get("created_at"),
                "finish_by": item.get("finish_by"),
                "created_by": item.get("created_by"),
                "assigned_to": item.get("assigned_to"),
                "status": item.get("status")
            })

        return {
            "statusCode": 200,
            "body": json.dumps({"tasks": tasks})
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
