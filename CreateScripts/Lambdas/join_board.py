import json
import boto3
import time
from botocore.exceptions import ClientError

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Handles joining a board through a valid access code.
    Input JSON should contain:
    {
        "user_id": "<uuid>",
        "access_code": "<ABC123>"
    }
    """

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
        # Look up the access code entry
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
        # Verify board exists (owner row must exist)
        # ---------------------------------
        # Query for a PK that begins with USER# and SK=BOARD#board_id
        owner_query = table.scan(
            FilterExpression="SK = :sk AND begins_with(PK, :prefix)",
            ExpressionAttributeValues={
                ":sk": board_sk,
                ":prefix": "USER#"
            }
        ).get("Items", [])

        if not owner_query:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Board not found"})
            }

        owner_item = owner_query[0]
        owner_id = owner_item["owner_id"]

        # ---------------------------------
        # Check if the user is already a member
        # ---------------------------------
        existing_resp = table.get_item(Key={"PK": user_pk, "SK": board_sk})
        if "Item" in existing_resp:
            return {
                "statusCode": 409,
                "body": json.dumps({"error": "User already joined this board"})
            }

        # ---------------------------------
        # Add membership row
        # ---------------------------------
        membership_item = {
            "PK": user_pk,
            "SK": board_sk,
            "board_id": board_id,
            "user_id": user_id,
            "owner_id": owner_id,
            "role": "member",
            "joined_at": int(time.time())
        }

        table.put_item(Item=membership_item)

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Joined board successfully",
                "board_id": board_id,
                "owner_id": owner_id
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e.response["Error"])
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
