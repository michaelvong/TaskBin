import json
import boto3
import os

dynamodb = boto3.resource("dynamodb")

# --- DynamoDB single table name ---
TABLE_NAME = "TaskBin"

table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    user_id = event["pathParameters"]["user_id"]

    # 1) Get all membership rows for this user
    response = table.query(
        KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq(f"USER#{user_id}")
    )
    membership_items = response.get("Items", [])

    boards = []

    for item in membership_items:
        if not item["SK"].startswith("BOARD#"):
            continue

        board_id = item["board_id"]

        # 2) Load metadata for this board
        metadata_key = {
            "PK": f"BOARD#{board_id}",
            "SK": "METADATA"
        }
        metadata_item = table.get_item(Key=metadata_key).get("Item", {})

        # 3) Merge membership + metadata
        boards.append({
            "id": board_id,
            "name": (
                item.get("board_name")
                or metadata_item.get("board_name")
                or ""
            ),
            "description": (
                item.get("description")
                or metadata_item.get("description")
                or ""
            ),
            "role": item.get("role", "owner"),
            "joinedAt": item.get("joined_at"),
        })

    return {
        "statusCode": 200,
        "body": json.dumps({"boards": boards})
    }
