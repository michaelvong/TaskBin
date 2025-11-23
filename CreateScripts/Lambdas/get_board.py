import json
import boto3

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("TaskBin")

def lambda_handler(event, context):
    # Get path parameter (single ID) and query/body parameter (batch)
    path_board_id = event.get("pathParameters", {}).get("board_id")
    body = json.loads(event.get("body", "{}")) if event.get("body") else {}
    batch_ids = body.get("board_ids", [])

    # Determine IDs to fetch
    board_ids = [path_board_id] if path_board_id else batch_ids

    if not board_ids:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "No board_id or board_ids provided"})
        }

    try:
        # Prepare keys for DynamoDB batch_get_item
        keys = [{"PK": f"BOARD#{bid}", "SK": "METADATA"} for bid in board_ids]

        # DynamoDB batch fetch
        response = dynamodb.batch_get_item(
            RequestItems={
                "TaskBin": {
                    "Keys": keys
                }
            }
        )

        items = response["Responses"].get("TaskBin", [])

        # Map to metadata format
        boards = [
            {
                "id": item["board_id"],
                "name": item.get("board_name", ""),
                "description": item.get("description", ""),
                "owner_id": item.get("owner_id", ""),
                "created_at": item.get("created_at", "")
            }
            for item in items
        ]

        return {
            "statusCode": 200,
            "body": json.dumps({"boards": boards})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
