import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("TaskBin")

def lambda_handler(event, context):
    path_task_id = event.get("pathParameters", {}).get("task_id")
    body = json.loads(event.get("body", "{}")) if event.get("body") else {}
    batch_ids = body.get("task_ids", [])

    task_ids = [path_task_id] if path_task_id else batch_ids

    if not task_ids:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No task_id or task_ids provided"})
        }

    try:
        keys = [{"PK": f"TASK#{tid}", "SK": "METADATA"} for tid in task_ids]

        response = dynamodb.batch_get_item(
            RequestItems={
                "TaskBin": {
                    "Keys": keys
                }
            }
        )

        items = response["Responses"].get("TaskBin", [])

        tasks = [
            {
                "id": item["task_id"],
                "title": item.get("title", ""),
                "description": item.get("description", ""),
                "board_id": item.get("board_id", ""),
                "assigned_to": item.get("assigned_to", ""),
                "status": item.get("status", ""),
                "created_at": item.get("created_at", "")
            }
            for item in items
        ]

        return {
            "statusCode": 200,
            "body": json.dumps({"tasks": tasks})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
