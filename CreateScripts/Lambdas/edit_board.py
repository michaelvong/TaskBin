import json
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

def lambda_handler(event, context):
    """
    Lambda to edit board metadata.
    Path: PUT /boards/{board_id}

    Body JSON:
    {
        "user_id": "<uuid>",       # must be the owner
        "board_name": "<optional new name>",
        "description": "<optional new description>"
    }
    """
    try:
        # --- Grab board_id from URL path ---
        path_params = event.get("pathParameters", {})
        board_id = path_params.get("board_id")
        if not board_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing board_id in path"})}

        # --- Parse body ---
        body = json.loads(event.get("body", "{}"))
        user_id = body.get("user_id")
        new_name = body.get("board_name")
        new_description = body.get("description")

        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing user_id in body"})}

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

        # --- Prepare update expression ---
        update_expr = []
        expr_values = {}

        if new_name is not None:
            update_expr.append("board_name = :name")
            expr_values[":name"] = new_name
        if new_description is not None:
            update_expr.append("description = :desc")
            expr_values[":desc"] = new_description

        if not update_expr:
            return {"statusCode": 400, "body": json.dumps({"error": "No fields to update"})}

        update_expression_str = "SET " + ", ".join(update_expr)

        # --- 1️⃣ Update metadata row ---
        table.update_item(
            Key={"PK": board_pk, "SK": metadata_sk},
            UpdateExpression=update_expression_str,
            ExpressionAttributeValues=expr_values
        )

        # --- 2️⃣ Update all board-centric task rows ---
        board_tasks = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key("PK").eq(board_pk) &
                                   boto3.dynamodb.conditions.Key("SK").begins_with("TASK#")
        ).get("Items", [])

        for task in board_tasks:
            table.update_item(
                Key={"PK": task["PK"], "SK": task["SK"]},
                UpdateExpression=update_expression_str,
                ExpressionAttributeValues=expr_values
            )

        # --- 3️⃣ Update all user-centric task rows ---
        # Scan for USER#<user_id> rows for this board
        user_task_rows = table.scan(
            FilterExpression="SK = :sk AND begins_with(PK, :prefix)",
            ExpressionAttributeValues={
                ":sk": f"BOARD#{board_id}",
                ":prefix": "USER#"
            }
        ).get("Items", [])

        for user_task in user_task_rows:
            # Update only the user-centric tasks
            table.update_item(
                Key={"PK": user_task["PK"], "SK": user_task["SK"]},
                UpdateExpression=update_expression_str,
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
