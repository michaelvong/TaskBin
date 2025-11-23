import json
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    DELETE /boards/{boardId}
    Expects:
      - pathParameters.boardId
      - body.user_id (owner)
    """

    try:
        # ----------------------------
        # 1. Extract path parameter
        # ----------------------------
        path_params = event.get("pathParameters") or {}
        board_id = path_params.get("boardId")

        # ----------------------------
        # 2. Extract body (for user_id)
        # ----------------------------
        raw_body = event.get("body")
        if raw_body:
            body = json.loads(raw_body)
        else:
            body = {}

        user_id = body.get("user_id")

        if not user_id or not board_id:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Missing required fields: user_id, board_id"})
            }

        owner_pk = f"USER#{user_id}"
        board_pk = f"BOARD#{board_id}"
        board_sk = f"BOARD#{board_id}"

        # ----------------------------
        # 3. Verify board metadata
        # ----------------------------
        response = table.get_item(Key={"PK": board_pk, "SK": "METADATA"})
        board_item = response.get("Item")

        if not board_item:
            return {"statusCode": 404, "body": json.dumps({"error": "Board not found"})}

        # Only owner can delete
        if board_item.get("owner_id") != user_id:
            return {"statusCode": 403, "body": json.dumps({"error": "Only the owner can delete this board"})}

        # ----------------------------
        # 4. Delete (USER, BOARD) membership entry
        # ----------------------------
        table.delete_item(Key={"PK": owner_pk, "SK": board_sk})

        # ----------------------------
        # 5. Delete all (BOARD, USER) membership entries
        # ----------------------------
        member_resp = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={
                ":pk": board_pk,
                ":prefix": "USER#"
            }
        )

        items = member_resp.get("Items", [])

        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})

        # ----------------------------
        # 6. Delete metadata row
        # ----------------------------
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
