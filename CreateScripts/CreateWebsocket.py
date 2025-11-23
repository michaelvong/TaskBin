import boto3
from botocore.exceptions import ClientError
import json
import os

REGION = "us-west-1"

apigateway = boto3.client("apigatewayv2", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

# ----------------------------
# Resolve File Paths
# ----------------------------
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))      # TaskBin/CreateScripts/
BASE_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))   # TaskBin/
API_ID_FILE = os.path.join(BASE_DIR, "api_id.json")
LAMBDA_ARNS_FILE = os.path.join(SCRIPT_DIR, "lambda_arns.json")


def load_lambda_arns():
    """Load Lambda ARNs from lambda_arns.json"""
    if not os.path.exists(LAMBDA_ARNS_FILE):
        raise FileNotFoundError(f"{LAMBDA_ARNS_FILE} not found")

    with open(LAMBDA_ARNS_FILE, "r") as f:
        return json.load(f)


def save_websocket_api_id(api_id):
    """Write websocket_api_id into api_id.json"""
    existing = {}

    if os.path.exists(API_ID_FILE):
        try:
            with open(API_ID_FILE, "r") as f:
                existing = json.load(f)
        except json.JSONDecodeError:
            existing = {}

    existing["websocket_api_id"] = api_id

    with open(API_ID_FILE, "w") as f:
        json.dump(existing, f, indent=4)

    print(f"💾 Saved websocket_api_id={api_id} into api_id.json")


def allow_api_to_call_lambda(lambda_name, api_id, region="us-west-1"):
    """Grants API Gateway permission to invoke the lambda."""
    sts = boto3.client("sts")
    account_id = sts.get_caller_identity()["Account"]

    source_arn = f"arn:aws:execute-api:{region}:{account_id}:{api_id}/*"

    try:
        lambda_client.add_permission(
            FunctionName=lambda_name,
            StatementId=f"{lambda_name}_WS_PERM",
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=source_arn,
        )
        print(f"✅ Permission added for {lambda_name} → {source_arn}")

    except lambda_client.exceptions.ResourceConflictException:
        print(f"ℹ️ Permission already exists for {lambda_name}")

    except ClientError as e:
        print(f"❌ Error adding permission for {lambda_name}: {e}")


def create_route_and_integration(api_id, route_key, lambda_arn):
    """Create route + lambda integration for WebSockets."""
    integration = apigateway.create_integration(
        ApiId=api_id,
        IntegrationType="AWS_PROXY",
        IntegrationUri=lambda_arn,
        IntegrationMethod="POST",
        PayloadFormatVersion="1.0"
    )

    integration_id = integration["IntegrationId"]

    apigateway.create_route(
        ApiId=api_id,
        RouteKey=route_key,
        Target=f"integrations/{integration_id}"
    )

    print(f"✅ Route '{route_key}' → Lambda: {lambda_arn}")


def create_websocket_api(connect_arn, disconnect_arn, sendmessage_arn):
    """Creates the WebSocket API with all routes and deploys it."""

    # 1️⃣ Create WebSocket API
    try:
        api_response = apigateway.create_api(
            Name="TaskBinWebSocketAPI",
            ProtocolType="WEBSOCKET",
            RouteSelectionExpression="$request.body.action"
        )
        api_id = api_response["ApiId"]
        api_endpoint = api_response["ApiEndpoint"]

        print(f"🚀 Created WebSocket API: {api_id}")
        print(f"🔌 Endpoint: {api_endpoint}")

    except ClientError as e:
        print(f"❌ Failed to create WebSocket API: {e}")
        return None

    # 2️⃣ Permissions
    allow_api_to_call_lambda("TaskBin_SocketConnect", api_id)
    allow_api_to_call_lambda("TaskBin_SocketDisconnect", api_id)
    allow_api_to_call_lambda("TaskBin_SocketSendmsg", api_id)

    # 3️⃣ Routes
    create_route_and_integration(api_id, "$connect", connect_arn)
    create_route_and_integration(api_id, "$disconnect", disconnect_arn)
    create_route_and_integration(api_id, "sendMessage", sendmessage_arn)

    # ⭐ REQUIRED or else you get "Forbidden"
    create_route_and_integration(api_id, "$default", sendmessage_arn)

    # 4️⃣ Deploy API → prod
    try:
        deployment = apigateway.create_deployment(
            ApiId=api_id,
            Description="Initial WebSocket deployment"
        )

        apigateway.create_stage(
            ApiId=api_id,
            StageName="prod",
            DeploymentId=deployment["DeploymentId"]
        )

        print("📦 WebSocket API deployed to stage → prod")

    except ClientError as e:
        print(f"❌ Failed deployment: {e}")
        return None


    # ---------------------------------------------
    # 5️⃣ Inject WS_ENDPOINT env var into SendMsg Lambda
    # ---------------------------------------------
    ws_endpoint = f"https://{api_id}.execute-api.us-west-1.amazonaws.com/prod"
    print(f"🌐 Injecting WS_ENDPOINT={ws_endpoint} into TaskBin_SocketSendmsg")

    lambda_client.update_function_configuration(
        FunctionName="TaskBin_SocketSendmsg",
        Environment={
            "Variables": {
                "WS_ENDPOINT": ws_endpoint
            }
        }
    )

    print("🔧 WS_ENDPOINT successfully set on SendMsg Lambda")


    # Save API ID for future builds
    save_websocket_api_id(api_id)

    return {"api_id": api_id, "endpoint": api_endpoint}



def setup_websocket_api():
    lambda_arns = load_lambda_arns()

    return create_websocket_api(
        lambda_arns["TaskBin_SocketConnect"],
        lambda_arns["TaskBin_SocketDisconnect"],
        lambda_arns["TaskBin_SocketSendmsg"]
    )


if __name__ == "__main__":
    setup_websocket_api()
