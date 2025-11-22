import json
import uuid
import boto3
from datetime import datetime

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("TaskBin")

def lambda_handler(event, context):
    body = json.loads(event["body"])

    user_id = body.get("user_id")
    board_name = body.get("name")
    description = body.get("description", "")

    if not user_id or not board_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing user_id or board name"})
        }

    board_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    metadata = {
        "PK": f"BOARD#{board_id}",
        "SK": "METADATA",
        "type": "board",
        "board_id": board_id,
        "board_name": board_name,
        "description": description,
        "created_at": now,
        "owner_id": user_id,
    }

    membership = {
        "PK": f"USER#{user_id}",
        "SK": f"BOARD#{board_id}",
        "type": "membership",
        "board_id": board_id,
        "user_id": user_id,
        "role": "owner",
        "joined_at": now,
    }

    table.put_item(Item=metadata)
    table.put_item(Item=membership)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "board": {
                "id": board_id,
                "name": board_name,
                "description": description
            }
        })
    }
