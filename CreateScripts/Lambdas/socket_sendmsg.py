import json
import boto3

TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

apigateway = boto3.client("apigatewaymanagementapi", endpoint_url="https://<api-id>.execute-api.us-west-1.amazonaws.com/dev")

def lambda_handler(event, context):
    """
    Lambda for sending a message to all connections of a board.
    Expects:
    {
        "board_id": "<board-uuid>",
        "user_id": "<sender-uuid>",
        "message": "<text>"
    }
    """
    try:
        body = json.loads(event.get("body") or event)

        board_id = body.get("board_id")
        user_id = body.get("user_id")
        message = body.get("message")

        if not board_id or not user_id or not message:
            return {"statusCode": 400, "body": "Missing board_id, user_id, or message"}

        # Query all connections for this board
        response = table.query(
            KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
            ExpressionAttributeValues={
                ":pk": f"BOARD#{board_id}",
                ":sk": "CONNECTION#"
            }
        )
        connections = response.get("Items", [])

        # Send message to all connections
        for conn in connections:
            connection_id = conn["SK"].split("#")[1]
            try:
                apigateway.post_to_connection(
                    Data=json.dumps({"user_id": user_id, "message": message}),
                    ConnectionId=connection_id
                )
            except apigateway.exceptions.GoneException:
                # Connection is stale, remove it
                table.delete_item(Key={"PK": conn["PK"], "SK": conn["SK"]})

        return {"statusCode": 200, "body": "Message sent"}

    except Exception as e:
        print("Error in sendMessage Lambda:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
