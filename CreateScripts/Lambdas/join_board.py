import json
import boto3
import time
from botocore.exceptions import ClientError

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):

    try:
        # ---------------------------------
        # Parse request body
        # ---------------------------------
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        access_code = body.get("access_code")

        if not user_id or not access_code:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, access_code"})
            }

        user_pk = f"USER#{user_id}"
        access_pk = f"ACCESS_CODE#{access_code}"

        # ---------------------------------
        # Look up ACCESS entry
        # ---------------------------------
        code_resp = table.get_item(Key={"PK": access_pk, "SK": "ACCESS"})
        code_item = code_resp.get("Item")

        if not code_item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Invalid or expired access code"})
            }

        board_id = code_item.get("board_id")
        if not board_id:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Corrupted access code entry: missing board_id"})
            }

        board_sk = f"BOARD#{board_id}"

        # ---------------------------------
        # Verify the board exists
        # (owner record must exist, but we don't use it)
        # ---------------------------------
        owner_item = table.scan(
            FilterExpression="SK = :sk AND begins_with(PK, :prefix)",
            ExpressionAttributeValues={
                ":sk": board_sk,
                ":prefix": "USER#"
            }
        ).get("Items", [])

        if not owner_item:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Board not found"})
            }

        # We do NOT extract owner_id or do anything with it anymore.

        # ---------------------------------
        # Check if user already belongs to the board
        # ---------------------------------
        existing_resp = table.get_item(Key={"PK": user_pk, "SK": board_sk})
        if "Item" in existing_resp:
            return {
                "statusCode": 409,
                "body": json.dumps({"error": "User already joined this board"})
            }

        now_ts = int(time.time())

        # ---------------------------------
        # Add membership rows (USER->BOARD and BOARD->USER)
        # ---------------------------------
        table.put_item(
            Item={
                "PK": user_pk,
                "SK": board_sk,
                "board_id": board_id,
                "user_id": user_id,
                "role": "member",
                "joined_at": now_ts,
                "type": "membership"
            }
        )

        table.put_item(
            Item={
                "PK": f"BOARD#{board_id}",
                "SK": f"USER#{user_id}",
                "board_id": board_id,
                "user_id": user_id,
                "role": "member",
                "joined_at": now_ts,
                "type": "board_user"
            }
        )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Joined board successfully",
                "board_id": board_id
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e.response["Error"])
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
