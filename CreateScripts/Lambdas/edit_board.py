import json
import boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to edit board metadata.
    Input JSON:
    {
        "user_id": "<uuid>",      # must be the owner
        "board_id": "<board-uuid>",
        "board_name": "<optional new name>",
        "description": "<optional new description>"
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
        new_name = body.get("board_name")
        new_description = body.get("description")

        if not user_id or not board_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing required fields: user_id, board_id"})}

        board_pk = f"BOARD#{board_id}"
        metadata_sk = "METADATA"

        # --- Get board metadata ---
        metadata_resp = table.get_item(Key={"PK": board_pk, "SK": metadata_sk})
        metadata_item = metadata_resp.get("Item")
        if not metadata_item:
            return {"statusCode": 404, "body": json.dumps({"error": "Board metadata not found"})}

        # --- Check ownership ---
        if metadata_item.get("owner_id") != user_id:
            return {"statusCode": 403, "body": json.dumps({"error": "Only the owner can edit the board"})}

        # --- Prepare update expressions ---
        update_expr = []
        expr_values = {}

        if new_name is not None:
            update_expr.append("board_name = :name")
            expr_values[":name"] = new_name
        if new_description is not None:
            update_expr.append("description = :desc")
            expr_values[":desc"] = new_description

        if update_expr:
            # --- Update metadata row ---
            table.update_item(
                Key={"PK": board_pk, "SK": metadata_sk},
                UpdateExpression="SET " + ", ".join(update_expr),
                ExpressionAttributeValues=expr_values
            )

            # --- Update all user-centric board rows ---
            # Scan all USER#<user_id> rows with this board SK
            member_rows = table.scan(
                FilterExpression="SK = :sk AND begins_with(PK, :prefix)",
                ExpressionAttributeValues={
                    ":sk": f"BOARD#{board_id}",
                    ":prefix": "USER#"
                }
            ).get("Items", [])

            with table.batch_writer() as batch:
                for member in member_rows:
                    batch.update_item(
                        Key={"PK": member["PK"], "SK": member["SK"]},
                        UpdateExpression="SET " + ", ".join(update_expr),
                        ExpressionAttributeValues=expr_values
                    )

        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": f"Board {board_id} updated successfully",
                "board_id": board_id
            })
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
