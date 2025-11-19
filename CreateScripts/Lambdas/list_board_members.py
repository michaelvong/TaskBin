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
    Input JSON:
    {
        "board_id": "<board-uuid>"
    }
    Returns:
    [
        {
            "user_id": "<uuid>",
            "role": "owner/member",
            "joined_at": "<timestamp>"  # may be None for owner
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
        if not board_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing required field: board_id"})}

        board_sk = f"BOARD#{board_id}"

        # Scan for all USER# PKs with this board SK
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
                "joined_at": item.get("joined_at")  # may be None for owner
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
