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
    Deletes the 3 entries created by create_board:
    - (USER, BOARD)
    - (BOARD, USER)
    - (BOARD, METADATA)
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
        board_pk = f"BOARD#{board_id}"
        board_sk = f"BOARD#{board_id}"

        # --- Get the board metadata to verify ownership ---
        response = table.get_item(Key={"PK": board_pk, "SK": "METADATA"})
        board_item = response.get("Item")

        if not board_item:
            return {"statusCode": 404, "body": json.dumps({"error": "Board not found"})}

        if board_item.get("owner_id") != user_id:
            return {"statusCode": 403, "body": json.dumps({"error": "Only the owner can delete this board"})}

        # --- Delete (USER, BOARD) membership entry ---
        table.delete_item(Key={"PK": owner_pk, "SK": board_sk})

        # --- Delete (BOARD, USER) reverse membership entries ---
        # Query all SKs that start with USER# under this board PK
        response = table.query(
            KeyConditionExpression="PK = :board_pk AND begins_with(SK, :user_prefix)",
            ExpressionAttributeValues={
                ":board_pk": board_pk,
                ":user_prefix": "USER#"
            }
        )
        board_user_items = response.get("Items", [])

        # Batch delete all (BOARD, USER) entries
        with table.batch_writer() as batch:
            for item in board_user_items:
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

        # --- Delete (BOARD, METADATA) entry ---
        table.delete_item(Key={"PK": board_pk, "SK": "METADATA"})

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Board {board_id} and all memberships deleted successfully"
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
