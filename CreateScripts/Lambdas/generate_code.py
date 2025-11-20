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
def generate_unique_code():
    while True:
        code = generate_access_code()
        pk = f"ACCESS_CODE#{code}"

        resp = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq(pk),
            Limit=1
        )
        if resp.get("Count", 0) == 0:
            return code


def lambda_handler(event, context):

    try:
        print("EVENT:", event)
        # ----------------------------------------------
        # Grab board_id ONLY from route path
        # ----------------------------------------------
        board_id = event.get("pathParameters", {}).get("board_id")

        # user_id still comes from body
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")

        if not board_id or not user_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing board_id (in route) or user_id (in body)"})
            }

        user_pk = f"USER#{user_id}"
        board_sk = f"BOARD#{board_id}"

        # ----------------------------------------------
        # Check if user is a member/owner of the board
        # ----------------------------------------------
        membership_resp = table.get_item(Key={"PK": user_pk, "SK": board_sk})
        if "Item" not in membership_resp:
            return {
                "statusCode": 403,
                "body": json.dumps({"error": "Not authorized: user is not a member/owner"})
            }

        # ----------------------------------------------
        # CHECK IF BOARD ALREADY HAS AN ACCESS CODE
        # PK = BOARD#<id> , SK = ACCESS
        # ----------------------------------------------
        board_access_resp = table.get_item(
            Key={"PK": f"BOARD#{board_id}", "SK": "ACCESS"}
        )

        existing_access = board_access_resp.get("Item")

        # reuse if exists and not expired
        if existing_access:
            expires = existing_access.get("expires_at")
            if expires:
                expires_dt = datetime.fromisoformat(expires)
                if expires_dt > datetime.now(timezone.utc):
                    # still valid → reuse
                    return {
                        "statusCode": 200,
                        "body": json.dumps({
                            "message": "Existing access code reused",
                            "access_code": existing_access["access_code"],
                            "expires_at": existing_access["expires_at"]
                        })
                    }

        # ----------------------------------------------
        # Otherwise → create a NEW access code
        # ----------------------------------------------
        unique_code = generate_unique_code()
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(hours=1)
        ttl_epoch = int(expires_at.timestamp())

        access_pk = f"ACCESS_CODE#{unique_code}"

        # 1) (BOARD, ACCESS)
        table.put_item(
            Item={
                "PK": f"BOARD#{board_id}",
                "SK": "ACCESS",
                "type": "board_access",
                "access_code": unique_code,
                "board_id": board_id,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "ttl": ttl_epoch
            }
        )

        # 2) (ACCESS_CODE, ACCESS)
        table.put_item(
            Item={
                "PK": access_pk,
                "SK": "ACCESS",
                "type": "access_code_meta",
                "access_code": unique_code,
                "board_id": board_id,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "ttl": ttl_epoch
            }
        )

        # 3) (ACCESS_CODE, BOARD)
        table.put_item(
            Item={
                "PK": access_pk,
                "SK": f"BOARD#{board_id}",
                "type": "access_code_link",
                "access_code": unique_code,
                "board_id": board_id,
                "created_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
                "ttl": ttl_epoch
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "New access code created",
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
