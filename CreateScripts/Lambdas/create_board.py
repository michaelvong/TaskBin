import json
import boto3
import uuid
from botocore.exceptions import ClientError
from datetime import datetime, timezone

# --- DynamoDB single table name ---
TABLE_NAME = "TaskBin"

# --- Initialize DynamoDB resource ---
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Create a board with 3 entries:

    1. (USER, BOARD)
       PK = USER#<user_id>
       SK = BOARD#<board_id>

    2. (BOARD, USER)
       PK = BOARD#<board_id>
       SK = USER#<user_id>

    3. (BOARD, METADATA)
       PK = BOARD#<board_id>
       SK = METADATA
    """

    try:
        # Parse body from API Gateway or direct test
        body = json.loads(event["body"]) if "body" in event else event

        user_id = body.get("user_id")
        board_name = body.get("board_name")
        description = body.get("description", "")

        if not user_id or not board_name:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, board_name"})
            }

        # Generate a unique board ID
        board_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # ----------------------------------------------------------------------
        # 1. USER → BOARD membership entry
        # ----------------------------------------------------------------------
        user_board_item = {
            "PK": f"USER#{user_id}",
            "SK": f"BOARD#{board_id}",
            "type": "membership",
            "board_id": board_id,
            "user_id": user_id,
            "role": "owner",
            "joined_at": now
        }

        # ----------------------------------------------------------------------
        # 2. BOARD → USER reverse membership
        # ----------------------------------------------------------------------
        board_user_item = {
            "PK": f"BOARD#{board_id}",
            "SK": f"USER#{user_id}",
            "type": "board_user",
            "board_id": board_id,
            "user_id": user_id,
            "role": "owner",
            "joined_at": now
        }

        # ----------------------------------------------------------------------
        # 3. BOARD → METADATA entry
        # ----------------------------------------------------------------------
        board_metadata_item = {
            "PK": f"BOARD#{board_id}",
            "SK": "METADATA",
            "type": "board_metadata",
            "board_id": board_id,
            "board_name": board_name,
            "description": description,
            "owner_id": user_id,
            "created_at": now,
        }

        # ----------------------------------------------------------------------
        # Write all 3 in a DynamoDB transaction (atomic)
        # ----------------------------------------------------------------------
        dynamodb.meta.client.transact_write_items(
            TransactItems=[
                {"Put": {"TableName": TABLE_NAME, "Item": user_board_item}},
                {"Put": {"TableName": TABLE_NAME, "Item": board_user_item}},
                {"Put": {"TableName": TABLE_NAME, "Item": board_metadata_item}}
            ]
        )

        # ----------------------------------------------------------------------
        # Success Response
        # ----------------------------------------------------------------------
        return {
            "statusCode": 201,
            "body": json.dumps({
                "message": "Board created successfully",
                "board_id": board_id,
                "board_name": board_name
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
