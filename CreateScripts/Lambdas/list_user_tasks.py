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
    user_id is grabbed from the route: /users/{user_id}/tasks
    Optional filters: board_id, task_status
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
            "task_status": "<task status>",
            "metadata": { ... }  # Task metadata
        },
        ...
    ]
    """
    try:
        # -----------------------------
        # Grab user_id from the route
        # -----------------------------
        path_params = event.get("pathParameters", {})
        user_id = path_params.get("user_id")
        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing user_id (in route)"})}

        # -----------------------------
        # Parse body for optional filters
        # -----------------------------
        if "body" in event and event["body"]:
            body = json.loads(event["body"])
        else:
            body = {}

        board_filter = body.get("board_id")
        task_status_filter = body.get("task_status")

        user_pk = f"USER#{user_id}"
        sk_prefix = "TASK#"

        # -----------------------------
        # Query all tasks for the user
        # -----------------------------
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
        if task_status_filter:
            items = [item for item in items if item.get("task_status") == task_status_filter]

        # -----------------------------
        # Format output and include metadata
        # -----------------------------
        tasks = []
        for item in items:
            task_id = item.get("task_id")
            # Fetch task metadata
            metadata_resp = table.get_item(Key={"PK": f"TASK#{task_id}", "SK": "METADATA"})
            metadata_item = metadata_resp.get("Item", {})

            tasks.append({
                "task_id": task_id,
                "board_id": item.get("board_id"),
                "title": item.get("title"),
                "description": item.get("description"),
                "created_at": item.get("created_at"),
                "finish_by": item.get("finish_by"),
                "created_by": item.get("created_by"),
                "assigned_to": item.get("assigned_to"),
                "task_status": item.get("task_status"),
                "metadata": metadata_item
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
