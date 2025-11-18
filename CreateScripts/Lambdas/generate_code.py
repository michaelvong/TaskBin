import json
import boto3
import random
import string
from datetime import datetime, timedelta, timezone
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


# -------------------------------------------------------
# Helper: generate random access code (3 letters + 3 digits)
# -------------------------------------------------------
def generate_access_code():
    letters = ''.join(random.choices(string.ascii_uppercase, k=3))
    numbers = ''.join(random.choices(string.digits, k=3))
    code_list = list(letters + numbers)
    random.shuffle(code_list)
    return ''.join(code_list)


# -------------------------------------------------------
# Helper: generate a unique access code (no collisions)
# -------------------------------------------------------
def generate_unique_code(board_id):
    while True:
        code = generate_access_code()
        pk = f"ACCESS_CODE#{code}"

        # Check if this code already exists for this board
        resp = table.get_item(Key={"PK": pk, "SK": f"BOARD#{board_id}"})
        if "Item" not in resp:
            return code


def lambda_handler(event, context):
    """
    Creates a single access code entry with TTL of 1 hour:
    PK = ACCESS_CODE#<code>
    SK = BOARD#<board_id>
    """
    try:
        # Parse event body
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        board_id = body.get("board_id")

        if not board_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required field: board_id"})
            }

        # -------------------------------------------------------
        # Generate unique access code
        # -------------------------------------------------------
        unique_code = generate_unique_code(board_id)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)
        ttl_epoch = int(expires_at.timestamp())

        # -------------------------------------------------------
        # Create (ACCESS_CODE, BOARD) entry with TTL
        # -------------------------------------------------------
        table.put_item(
            Item={
                "PK": f"ACCESS_CODE#{unique_code}",
                "SK": f"BOARD#{board_id}",
                "type": "access_code",
                "board_id": board_id,
                "access_code": unique_code,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "ttl": ttl_epoch  # DynamoDB TTL attribute
            }
        )

        # -------------------------------------------------------
        # Return success
        # -------------------------------------------------------
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Access code created",
                "access_code": unique_code,
                "expires_at": expires_at.isoformat()
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
