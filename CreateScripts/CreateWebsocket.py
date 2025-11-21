import boto3
from botocore.exceptions import ClientError
import json
import os

REGION = "us-west-1"

apigateway = boto3.client("apigatewayv2", region_name=REGION)

# ----------------------------
# Resolve File Paths
# ----------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))  # TaskBin/CreateScripts/
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))  # TaskBin/
ROUTES_DIR = os.path.join(SCRIPT_DIR, "routes")  # TaskBin/CreateScripts/routes/

API_ID_FILE = os.path.join(BASE_DIR, "api_id.json")  # TaskBin/api_id.json
LAMBDA_ARNS_FILE = os.path.join(SCRIPT_DIR, "lambda_arns.json")  # TaskBin/CreateScripts/lambda_arns.json


def load_lambda_arns():
    """Load Lambda ARNs from lambda_arns.json"""
    if not os.path.exists(LAMBDA_ARNS_FILE):
        raise FileNotFoundError(f"{LAMBDA_ARNS_FILE} not found")

    with open(LAMBDA_ARNS_FILE, "r") as f:
        return json.load(f)


def save_websocket_api_id(api_id):
    """Write or update websocket_api_id inside api_id.json."""
    existing = {}
    if os.path.exists(API_ID_FILE):
        with open(API_ID_FILE, "r") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = {}
    existing["websocket_api_id"] = api_id
    with open(API_ID_FILE, "w") as f:
        json.dump(existing, f, indent=4)
    print(f"💾 Saved websocket_api_id to api_id.json: {api_id}")


def create_websocket_api(connect_arn, disconnect_arn, sendmessage_arn):
    """
    Creates a WebSocket API and attaches $connect, $disconnect, sendMessage routes.
    Returns api_id and endpoint.
    """

    def create_route_and_integration(api_id, route_key, lambda_arn):
        integration_response = apigateway.create_integration(
            ApiId=api_id,
            IntegrationType="AWS_PROXY",
            IntegrationUri=lambda_arn,
            IntegrationMethod="POST"
        )
        integration_id = integration_response["IntegrationId"]

        apigateway.create_route(
            ApiId=api_id,
            RouteKey=route_key,
            Target=f'integrations/{integration_id}'
        )

        print(f"✅ Route '{route_key}' created and linked to Lambda: {lambda_arn}")

    # Create the WebSocket API
    try:
        api_response = apigateway.create_api(
            Name="TaskBinWebSocketAPI",
            ProtocolType="WEBSOCKET",
            RouteSelectionExpression="$request.body.action"
        )
        api_id = api_response["ApiId"]
        api_endpoint = api_response["ApiEndpoint"]
        print(f"✅ WebSocket API created: {api_id} | Endpoint: {api_endpoint}")
    except ClientError as e:
        print(f"❌ Failed to create WebSocket API: {e}")
        return None

    # Create routes
    create_route_and_integration(api_id, "$connect", connect_arn)
    create_route_and_integration(api_id, "$disconnect", disconnect_arn)
    create_route_and_integration(api_id, "sendMessage", sendmessage_arn)

    # Deploy
    try:
        deployment = apigateway.create_deployment(
            ApiId=api_id,
            Description="Initial deployment"
        )
        apigateway.create_stage(
            ApiId=api_id,
            StageName="dev",
            DeploymentId=deployment["DeploymentId"]
        )
        print(f"🚀 WebSocket API deployed to stage 'dev'")
    except ClientError as e:
        print(f"❌ Failed to deploy WebSocket API: {e}")
        return None

    # Save the WebSocket API ID
    save_websocket_api_id(api_id)
    return {"api_id": api_id, "endpoint": api_endpoint}


def setup_websocket_api():
    """
    Main function to set up the WebSocket API with routes.
    Loads ARNs automatically from lambda_arns.json
    """
    lambda_arns = load_lambda_arns()
    connect_arn = lambda_arns["TaskBin_SocketConnect"]
    disconnect_arn = lambda_arns["TaskBin_SocketDisconnect"]
    sendmessage_arn = lambda_arns["TaskBin_SocketSendmsg"]

    return create_websocket_api(connect_arn, disconnect_arn, sendmessage_arn)


if __name__ == "__main__":
    setup_websocket_api()
