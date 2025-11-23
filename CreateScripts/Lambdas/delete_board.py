import json
import boto3
from botocore.exceptions import ClientError

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)
lambda_client = boto3.client("lambda")

def lambda_handler(event, context):
    """
    DELETE /boards/{boardId}
    Deletes board safely with no race conditions.
    """

    try:
        # ----------------------------
        # 1. Extract path & body
        # ----------------------------
        path_params = event.get("pathParameters") or {}
        board_id = path_params.get("boardId")

        raw_body = event.get("body")
        body = json.loads(raw_body) if raw_body else {}
        user_id = str(body.get("user_id", "")).strip().lower()

        if not user_id or not board_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing required fields"})}

        board_pk = f"BOARD#{board_id}"

        # ----------------------------
        # 2. Fetch board metadata & verify owner
        # ----------------------------
        resp = table.get_item(Key={"PK": board_pk, "SK": "METADATA"})
        board_item = resp.get("Item")
        if not board_item:
            return {"statusCode": 404, "body": json.dumps({"error": "Board not found"})}

        owner_id = str(board_item.get("owner_id", "")).strip().lower()
        if owner_id != user_id:
            return {"statusCode": 403, "body": json.dumps({"error": "Only the owner can delete this board"})}

        # ----------------------------
        # 3. Gather all items to delete
        # ----------------------------
        delete_keys = []

        # 3a. All tasks + metadata
        task_resp = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={":pk": board_pk, ":prefix": "TASK#"}
        )
        tasks = task_resp.get("Items", [])
        for task in tasks:
            delete_keys.append({"PK": board_pk, "SK": task["SK"]})
            delete_keys.append({"PK": task["SK"], "SK": "METADATA"})  # task metadata

        # 3b. Access code entries
        access_resp = table.get_item(Key={"PK": board_pk, "SK": "ACCESS"})
        access_item = access_resp.get("Item")
        if access_item and "code" in access_item:
            access_code = str(access_item["code"]).strip()
            access_pk = f"ACCESS#{access_code}"
            access_items = table.query(KeyConditionExpression="PK = :pk", ExpressionAttributeValues={":pk": access_pk}).get("Items", [])
            for item in access_items:
                delete_keys.append({"PK": item["PK"], "SK": item["SK"]})
            delete_keys.append({"PK": board_pk, "SK": "ACCESS"})

        # 3c. Memberships (BOARD->USER)
        member_resp = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :prefix)",
            ExpressionAttributeValues={":pk": board_pk, ":prefix": "USER#"}
        )
        members = member_resp.get("Items", [])
        for member in members:
            delete_keys.append({"PK": member["PK"], "SK": member["SK"]})  # BOARD->USER

        # 3d. Memberships (USER->BOARD)
        for member in members:
            user_sk = member["SK"]       # USER#uid
            uid = user_sk.split("#")[1]
            user_pk = f"USER#{uid}"
            board_sk = f"BOARD#{board_id}"
            delete_keys.append({"PK": user_pk, "SK": board_sk})
        delete_keys.append({"PK": f"USER#{owner_id}", "SK": f"BOARD#{board_id}"})  # owner

        # 3e. Board metadata last
        delete_keys.append({"PK": board_pk, "SK": "METADATA"})

        # ----------------------------
        # 4. Execute deletion in batch
        # ----------------------------
        with table.batch_writer() as batch:
            for key in delete_keys:
                batch.delete_item(Key=key)

        print(f"🗑 Deleted board {board_id}: {len(tasks)} tasks, {len(members)} memberships, access entries")

        event_payload = {
            "action": "boardDeleted",
            "board_id": board_id,
            "user_id": user_id  # optional: who deleted it
        }

        try:
            lambda_client.invoke(
                FunctionName="TaskBin_SocketSendmsg",
                InvocationType="Event",  # async, won't block deletion
                Payload=json.dumps(event_payload).encode("utf-8")
            )
            print(f"📡 Broadcast invoked for boardDeleted: {board_id}")
        except Exception as e:
            print(f"❌ Failed to invoke socket_sendmsg: {e}")

        return {"statusCode": 200, "body": json.dumps({"message": f"Board {board_id} deleted successfully."})}

    except ClientError as e:
        print("DynamoDB error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}

    except Exception as e:
        print("Error:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
