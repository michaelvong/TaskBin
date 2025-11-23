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
    board_id is taken from the route path.
    Optional "status" filter comes from body.
    """
    try:
        print("EVENT:", json.dumps(event))  # helpful for debugging

        # ----------------------------
        # 1. Get board_id from URL path
        # ----------------------------
        board_id = None
        if event.get("pathParameters"):
            board_id = event["pathParameters"].get("board_id")

        if not board_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing board_id (path parameter)"})
            }

        # ----------------------------
        # 2. Parse body for optional fields
        # ----------------------------
        if event.get("body"):
            try:
                body = json.loads(event["body"])
            except:
                body = {}
        else:
            body = {}

        status_filter = body.get("status")

        # ----------------------------
        # 3. Query DynamoDB
        # ----------------------------
        board_pk = f"BOARD#{board_id}"
        sk_prefix = "TASK#"

        response = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": board_pk,
                ":sk": sk_prefix
            }
        )

        items = response.get("Items", [])

        # ----------------------------
        # 4. Optional filter
        # ----------------------------
        if status_filter:
            items = [item for item in items if item.get("status") == status_filter]

        # ----------------------------
        # 5. Format response
        # ----------------------------
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
                "task_status": item.get("task_status")
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
