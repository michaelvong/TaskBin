import json
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB single table name ---
TABLE_NAME = "TaskBin"

# --- Initialize DynamoDB resource ---
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Lambda to delete a board from DynamoDB.
    Only the owner can delete the board.
    Deletes all user-centric rows using batch_writer with deduplication.
    Expects event to contain JSON body:
    {
        "user_id": "<owner-uuid>",
        "board_id": "<board-uuid>"
    }
    """

    try:
        # Parse input body
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

        owner_pk = f"USER#{user_id}"
        board_sk = f"BOARD#{board_id}"

        # --- Get the board item to verify ownership ---
        response = table.get_item(Key={"PK": owner_pk, "SK": board_sk})
        board_item = response.get("Item")

        if not board_item:
            return {"statusCode": 404, "body": json.dumps({"error": "Board not found"})}

        if board_item.get("owner_id") != user_id:
            return {"statusCode": 403, "body": json.dumps({"error": "Only the owner can delete this board"})}

        # --- Scan for all user-centric rows with this board SK ---
        member_rows = table.scan(
            FilterExpression="SK = :sk AND begins_with(PK, :prefix)",
            ExpressionAttributeValues={
                ":sk": board_sk,
                ":prefix": "USER#"
            }
        ).get("Items", [])

        # --- Deduplicate and prepare keys for batch delete ---
        unique_keys = set()
        # Add owner row
        unique_keys.add((owner_pk, board_sk))
        # Add member rows
        for member in member_rows:
            member_pk = member["PK"]
            if member_pk == owner_pk:
                continue  # skip owner
            unique_keys.add((member_pk, board_sk))

        # --- Delete all rows in batch ---
        with table.batch_writer() as batch:
            for pk, sk in unique_keys:
                batch.delete_item(Key={"PK": pk, "SK": sk})

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Board {board_id} and all memberships to board deleted successfully"
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
