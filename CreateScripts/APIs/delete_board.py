# APIs/delete_board.py

import json
import boto3
import os

# ---------------------------
# DynamoDB setup
# ---------------------------
TABLE_NAME = "TaskBin"
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

# ---------------------------
# Lambda ARN file
# ---------------------------
BASE_DIR = os.path.dirname(__file__)
ARN_FILE = os.path.join(BASE_DIR, "../lambda_arns.json")  # JSON file relative to APIs folder


def get_lambda_arn(lambda_name):
    """Reads lambda_arns.json and returns the ARN for the given Lambda name"""
    if not os.path.exists(ARN_FILE):
        raise FileNotFoundError(f"Lambda ARN file not found: {ARN_FILE}")

    with open(ARN_FILE, "r") as f:
        lambda_arns = json.load(f)

    arn = lambda_arns.get(lambda_name)
    if not arn:
        raise ValueError(f"Lambda ARN not found for {lambda_name}")
    return arn


# ---------------------------
# Lambda handler
# ---------------------------
def lambda_handler(event, context):
    """
    Lambda endpoint to delete a board.
    Expects JSON body:
    {
        "user_id": "<user-uuid>",
        "board_id": "<board-uuid>"
    }
    """
    try:
        if "body" in event:
            body = json.loads(event["body"])
        else:
            body = event

        user_id = body.get("user_id")
        board_id = body.get("board_id")

        if not user_id or not board_id:
            return {"statusCode": 400, "body": json.dumps({"error": "Missing required fields"})}

        pk = f"USER#{user_id}"
        sk = f"BOARD#{board_id}"

        response = table.delete_item(
            Key={"PK": pk, "SK": sk},
            ConditionExpression="attribute_exists(PK) AND attribute_exists(SK)"
        )

        return {"statusCode": 200, "body": json.dumps({"message": f"Board {board_id} deleted"})}

    except boto3.client("dynamodb").exceptions.ConditionalCheckFailedException:
        return {"statusCode": 404, "body": json.dumps({"error": "Board not found"})}
    except Exception as e:
        print("Error deleting board:", e)
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}


# ---------------------------
# Orchestrator API creation
# ---------------------------
def create_api(lambda_name="TaskBin_DeleteBoard", api_name=None):
    """
    Creates an AWS HTTP API Gateway endpoint and integrates it with the Lambda.
    lambda_name: Name of the Lambda as stored in lambda_arns.json
    api_name: optional name for the API
    Returns: dict with api_id and endpoint URL
    """
    lambda_arn = get_lambda_arn(lambda_name)

    if not api_name:
        api_name = "DeleteBoardAPI"

    apigw = boto3.client("apigatewayv2")

    # 1️⃣ Create the HTTP API
    api_resp = apigw.create_api(
        Name=api_name,
        ProtocolType="HTTP"
    )
    api_id = api_resp["ApiId"]

    # 2️⃣ Create Lambda integration
    integration_resp = apigw.create_integration(
        ApiId=api_id,
        IntegrationType="AWS_PROXY",
        IntegrationUri=lambda_arn,
        PayloadFormatVersion="2.0",
        IntegrationMethod="POST"
    )
    integration_id = integration_resp["IntegrationId"]

    # 3️⃣ Create route pointing to the integration
    route_resp = apigw.create_route(
        ApiId=api_id,
        RouteKey="POST /deleteBoard",
        Target=f"integrations/{integration_id}"
    )

    # 4️⃣ Deploy stage
    stage_resp = apigw.create_stage(
        ApiId=api_id,
        StageName="dev",
        AutoDeploy=True
    )

    endpoint = f"https://{api_id}.execute-api.{apigw.meta.region_name}.amazonaws.com/dev/deleteBoard"
    print(f"✅ Created API Gateway endpoint: {endpoint}")
    return {"api_id": api_id, "endpoint": endpoint}


# ---------------------------
# Orchestrator API deletion
# ---------------------------
def delete_api(api_id):
    """
    Deletes an AWS HTTP API Gateway endpoint given its api_id.
    api_id: ID of the API to delete
    Returns: dict with deletion status
    """
    if not api_id:
        raise ValueError("API ID must be provided to delete the API.")

    apigw = boto3.client("apigatewayv2")

    try:
        # Check if the API exists
        apis = apigw.get_apis()["Items"]
        if not any(api["ApiId"] == api_id for api in apis):
            print(f"⚠️ API {api_id} not found. Nothing to delete.")
            return {"status": "not_found", "api_id": api_id}

        # Delete the API
        apigw.delete_api(ApiId=api_id)
        print(f"✅ Deleted API {api_id}")
        return {"status": "deleted", "api_id": api_id}

    except Exception as e:
        print(f"Error deleting API {api_id}: {e}")
        return {"status": "error", "error": str(e), "api_id": api_id}
