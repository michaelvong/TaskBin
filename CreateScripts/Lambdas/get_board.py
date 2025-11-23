import json
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("TaskBin")


def lambda_handler(event, context):
    # Get ID from path OR from batch input
    path_board_id = event.get("pathParameters", {}).get("board_id")
    body = json.loads(event.get("body", "{}")) if event.get("body") else {}
    batch_ids = body.get("board_ids", [])

    # Determine which IDs to fetch
    board_ids = [path_board_id] if path_board_id else batch_ids

    if not board_ids:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No board_id or board_ids provided"})
        }

    try:
        result_boards = []

        for board_id in board_ids:

            pk = f"BOARD#{board_id}"

            # --------------------------------------------
            # Query ALL board rows (metadata + members)
            # --------------------------------------------
            resp = table.query(
                KeyConditionExpression=Key("PK").eq(pk)
            )
            items = resp.get("Items", [])

            if not items:
                continue

            # --------------------------------------------
            # Extract METADATA row
            # --------------------------------------------
            meta = next((i for i in items if i["SK"] == "METADATA"), None)
            if not meta:
                continue

            # --------------------------------------------
            # Extract MEMBERS (SK starts with USER#)
            # --------------------------------------------
            members = []
            for i in items:
                if i["SK"].startswith("USER#"):
                    members.append({
                        "user_id": i.get("user_id"),
                        "role": i.get("role", "member"),
                        "joined_at": i.get("joined_at"),
                    })

            # --------------------------------------------
            # Build final board object
            # --------------------------------------------
            result_boards.append({
                "id": meta.get("board_id", board_id),
                "name": meta.get("board_name", ""),
                "description": meta.get("description", ""),
                "owner_id": meta.get("owner_id", ""),
                "created_at": meta.get("created_at", ""),
                "members": members,
            })

        return {
            "statusCode": 200,
            "body": json.dumps({"boards": result_boards})
        }

    except Exception as e:
        print("ERROR:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
