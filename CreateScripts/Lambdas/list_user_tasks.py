import json
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to list tasks assigned to a user.
    Input JSON:
    {
        "user_id": "<uuid>",
        "board_id": "<optional board filter>",
        "status": "<optional status filter>"
    }
    Returns:
    [
        {
            "task_id": "<task-uuid>",
            "board_id": "<board-uuid>",
            "title": "<task title>",
            "description": "<optional>",
            "created_at": "<ISO timestamp>",
            "finish_by": "<ISO timestamp, optional>",
            "created_by": "<user id>",
            "assigned_to": "<user id>",
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

        user_id = body.get("user_id")
        board_filter = body.get("board_id")
        status_filter = body.get("status")

        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing required field: user_id"})}

        user_pk = f"USER#{user_id}"
        sk_prefix = "TASK#"

        # Query all tasks for the user
        response = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": user_pk,
                ":sk": sk_prefix
            }
        )

        items = response.get("Items", [])

        # Apply optional filters
        if board_filter:
            items = [item for item in items if item.get("board_id") == board_filter]
        if status_filter:
            items = [item for item in items if item.get("status") == status_filter]

        # Format output
        tasks = []
        for item in items:
            tasks.append({
                "task_id": item.get("task_id"),
                "board_id": item.get("board_id"),
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
