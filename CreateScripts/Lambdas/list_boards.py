import json
import boto3
from botocore.exceptions import ClientError

# --- DynamoDB table ---
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def lambda_handler(event, context):
    """
    Lambda to list all boards for a given user.
    user_id is grabbed from the route: /users/{user_id}/boards
    Returns:
    [
        {
            "board_id": "<board-uuid>",
            "board_name": "<name>",
            "role": "<owner/member>",
            "description": "<optional description>",
            "joined_at": "<timestamp>",
            "metadata": {
                "owner_id": "<uuid>",
                "created_at": "<ISO timestamp>",
                "other_board_fields": "..."
            }
        },
        ...
    ]
    """
    try:
        # -----------------------------
        # Grab user_id from the route
        # -----------------------------
        path_params = event.get("pathParameters", {})
        user_id = path_params.get("user_id")
        if not user_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing user_id (in route)"})}

        user_pk = f"USER#{user_id}"

        # -----------------------------
        # Query all board memberships for this user
        # -----------------------------
        response = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
            ExpressionAttributeValues={
                ":pk": user_pk,
                ":sk_prefix": "BOARD#"
            }
        )

        items = response.get("Items", [])

        boards = []
        for item in items:
            board_id = item.get("board_id")
            board_sk = f"BOARD#{board_id}"

            # -----------------------------
            # Fetch board metadata
            # -----------------------------
            metadata_resp = table.get_item(Key={"PK": board_sk, "SK": "METADATA"})
            metadata_item = metadata_resp.get("Item", {})

            boards.append({
                "board_id": board_id,
                "board_name": item.get("board_name"),
                "role": item.get("role"),
                "description": item.get("description"),
                "joined_at": item.get("joined_at"),
                "metadata": metadata_item  # full metadata
            })

        return {
            "statusCode": 200,
            "body": json.dumps({"boards": boards})
        }

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
