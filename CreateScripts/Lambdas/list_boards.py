import boto3
import json

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("TaskBin")

def lambda_handler(event, context):
    user_id = event["pathParameters"]["user_id"]

    # Step 1: Fetch USER#email → BOARD#id membership items
    pk = f"USER#{user_id}"
    response = table.query(
        KeyConditionExpression="PK = :pk",
        ExpressionAttributeValues={":pk": pk}
    )

    items = response.get("Items", [])
    boards = []

    for item in items:
        if item.get("type") != "membership":
            continue

        board_id = item["board_id"]

        # Step 2: Fetch BOARD#id metadata
        meta_resp = table.get_item(
            Key={"PK": f"BOARD#{board_id}", "SK": "METADATA"}
        )
        metadata = meta_resp.get("Item", {})

        boards.append({
            "id": board_id,
            "name": metadata.get("board_name", ""),
            "description": metadata.get("description", ""),
            "createdAt": metadata.get("created_at", ""),
            "role": item.get("role", "member"),
            "joinedAt": item.get("joined_at", "")
        })

    return {
        "statusCode": 200,
        "body": json.dumps({"boards": boards})
    }
