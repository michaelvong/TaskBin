import json
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to list all members of a board.
    board_id is taken from the route path like:
    /board/{board_id}/members
    """
    try:
        print("EVENT:", json.dumps(event))  # helpful for debugging

        # --- 1. Get board_id from URL path ---
        board_id = None
        if "pathParameters" in event and event["pathParameters"]:
            board_id = event["pathParameters"].get("board_id")

        if not board_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing board_id (path parameter)"})
            }

        # --- 2. Parse body (if needed later) ---
        if event.get("body"):
            try:
                body = json.loads(event["body"])
            except:
                body = {}
        else:
            body = {}

        board_sk = f"BOARD#{board_id}"

        # --- 3. Query DynamoDB for members ---
        response = table.scan(
            FilterExpression="SK = :sk AND begins_with(PK, :prefix)",
            ExpressionAttributeValues={
                ":sk": board_sk,
                ":prefix": "USER#"
            }
        )

        items = response.get("Items", [])

        members = []
        for item in items:
            members.append({
                "user_id": item.get("user_id"),
                "role": item.get("role"),
                "joined_at": item.get("joined_at")
            })

        return {
            "statusCode": 200,
            "body": json.dumps({"members": members})
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
