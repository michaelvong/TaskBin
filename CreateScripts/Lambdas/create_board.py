import json
import boto3
from datetime import datetime
import uuid
import os

dynamodb = boto3.resource("dynamodb")
# --- DynamoDB single table name ---
TABLE_NAME = "TaskBin"

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    print("DEBUG EVENT:", json.dumps(event))

    raw_body = event.get("body")
    if not raw_body:
        raw_body = "{}"

    try:
        body = json.loads(raw_body)
    except Exception as e:
        print("ERROR parsing body:", e)
        body = {}

    user_id = body.get("user_id")
    board_name = body.get("name")
    description = body.get("description", "")

    if not user_id or not board_name:
        return {"statusCode": 400, "body": "Missing user_id or name"}

    board_id = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    # --- 1) Metadata row (source of truth) ---
    metadata_item = {
        "PK": f"BOARD#{board_id}",
        "SK": "METADATA",
        "type": "board_metadata",
        "board_id": board_id,
        "board_name": board_name,
        "description": description,
        "created_at": now,
        "owner_id": user_id,
    }

    # --- 2) Membership row (relationship only) ---
    membership_item = {
        "PK": f"USER#{user_id}",
        "SK": f"BOARD#{board_id}",
        "type": "membership",
        "board_id": board_id,
        "user_id": user_id,
        "role": "owner",
        "joined_at": now,
    }

    table.put_item(Item=metadata_item)
    table.put_item(Item=membership_item)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "id": board_id,
            "name": board_name,
            "description": description,
        })
    }
