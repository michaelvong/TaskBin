import json
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to list all boards for a given user.
    Input JSON:
    {
        "user_id": "<uuid>"
    }
    Returns:
    [
        {
            "board_id": "<board-uuid>",
            "board_name": "<name>",
            "role": "<owner/member>",
            "description": "<optional description>",
            "joined_at": "<timestamp>"
        },
        ...
    ]
    """
    try:
        # Parse input body
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing required field: user_id"})}

        user_pk = f"USER#{user_id}"

        # Query for all board memberships for this user
        response = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": user_pk,
                ":sk_prefix": "BOARD#"
            }
        )

        items = response.get("Items", [])

        # Format results
        boards = []
        for item in items:
            boards.append({
                "board_id": item.get("board_id"),
                "board_name": item.get("board_name"),
                "role": item.get("role"),
                "description": item.get("description"),
                "joined_at": item.get("joined_at")
            })

        return {
            "statusCode": 200,
            "body": json.dumps({"boards": boards})
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
