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
def generate_unique_code(board_sk):
    """
    Generate an access code that does not already exist in DynamoDB.
    """
    while True:
        code = generate_access_code()
        pk = f"ACCESS_CODE#{code}"

        # Check if this code already exists for any board
        resp = table.get_item(Key={"PK": pk, "SK": board_sk})
        if "Item" not in resp:
            return code
        # Else collision — rare but possible—loop and try again


def lambda_handler(event, context):
    """
    Generates an access code for a board.
    Logic:
    - Validate user is a member/owner
    - Reuse existing unexpired access code if still active
    - Otherwise generate a new unique one
    - Store it in the board item (with expiration metadata)
    - Create a separate TTL-protected access code entry
    """
    try:
        # Parse event body
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        board_id = body.get("board_id")

        if not user_id or not board_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, board_id"})
            }

        # Keys
        user_pk = f"USER#{user_id}"
        board_sk = f"BOARD#{board_id}"

        # -------------------------------------------------------
        # 1️⃣ Validate user is a member of the board
        # -------------------------------------------------------
        user_board_resp = table.get_item(Key={"PK": user_pk, "SK": board_sk})
        user_board_item = user_board_resp.get("Item")

        if not user_board_item:
            return {"statusCode": 403, "body": json.dumps({"error": "User is not a member of this board"})}

        board_owner_id = user_board_item["owner_id"]
        owner_pk = f"USER#{board_owner_id}"

        # Main board row
        board_resp = table.get_item(Key={"PK": owner_pk, "SK": board_sk})
        board_item = board_resp.get("Item")

        if not board_item:
            return {"statusCode": 404, "body": json.dumps({"error": "Board not found"})}

        existing_code = board_item.get("access_code")
        expires_at = board_item.get("access_code_expires_at")

        now = datetime.now(timezone.utc)

        # -------------------------------------------------------
        # 2️⃣ Check if existing access code is still valid
        # -------------------------------------------------------
        if existing_code and expires_at:
            expiration_dt = datetime.fromisoformat(expires_at)

            if expiration_dt > now:
                # Check if access code entry exists
                code_pk = f"ACCESS_CODE#{existing_code}"
                entry = table.get_item(Key={"PK": code_pk, "SK": board_sk}).get("Item")

                if entry:
                    return {
                        "statusCode": 200,
                        "body": json.dumps({
                            "message": "Reusing existing access code",
                            "access_code": existing_code,
                            "expires_at": expires_at
                        })
                    }

        # -------------------------------------------------------
        # 3️⃣ Generate NEW unique access code (no duplicates)
        # -------------------------------------------------------
        unique_code = generate_unique_code(board_sk)

        new_expiration = now + timedelta(hours=1)
        new_expiration_str = new_expiration.isoformat()
        ttl_epoch = int(new_expiration.timestamp())

        # -------------------------------------------------------
        # 4️⃣ Update board item with new code
        # -------------------------------------------------------
        table.update_item(
            Key={"PK": owner_pk, "SK": board_sk},
            UpdateExpression="SET access_code = :c, access_code_expires_at = :e",
            ExpressionAttributeValues={
                ":c": unique_code,
                ":e": new_expiration_str
            }
        )

        # -------------------------------------------------------
        # 5️⃣ Store access code entry with TTL
        # PK = ACCESS_CODE#CODE
        # SK = BOARD#<board_id>
        # -------------------------------------------------------
        table.put_item(
            Item={
                "PK": f"ACCESS_CODE#{unique_code}",
                "SK": "ACCESS",
                "Type": "access_code",
                "board_id": board_id,
                "access_code": unique_code,
                "expires_at": new_expiration_str,
                "ttl": ttl_epoch
            }
        )

        # -------------------------------------------------------
        # 6️⃣ Return success
        # -------------------------------------------------------
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Generated new access code",
                "access_code": unique_code,
                "expires_at": new_expiration_str
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
