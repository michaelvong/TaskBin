import boto3
from botocore.exceptions import ClientError
import time

REGION = "us-west-1"  # Change if needed

apigateway = boto3.client("apigatewayv2", region_name=REGION)
lambda_client = boto3.client("lambda", region_name=REGION)

def create_websocket_api(connect_arn, disconnect_arn, sendmessage_arn):
    """
    Creates a WebSocket API and attaches the $connect, $disconnect, and sendMessage routes.
    Returns the WebSocket API ID and endpoint.
    """

    # --- Step 1: Create the WebSocket API ---
    try:
        api_response = apigateway.create_api(
            Name="TaskBinWebSocketAPI",
            ProtocolType="WEBSOCKET",
            RouteSelectionExpression="$request.body.action"  # determines route based on action
        )
        api_id = api_response["ApiId"]
        api_endpoint = api_response["ApiEndpoint"]
        print(f"✅ WebSocket API created: {api_id} | Endpoint: {api_endpoint}")
    except ClientError as e:
        print(f"❌ Failed to create WebSocket API: {e}")
        return None

    # --- Helper to create route and integration ---
    def create_route_and_integration(route_key, lambda_arn):
        # 1. Create Integration
        integration_response = apigateway.create_integration(
            ApiId=api_id,
            IntegrationType="AWS_PROXY",
            IntegrationUri=lambda_arn,
            IntegrationMethod="POST"
        )
        integration_id = integration_response["IntegrationId"]

        # 2. Create Route
        route_response = apigateway.create_route(
            ApiId=api_id,
            RouteKey=route_key,
            Target=f'integrations/{integration_id}'
        )

        print(f"✅ Route '{route_key}' created and linked to Lambda {lambda_arn}")
        return route_response

    # --- Step 2: Create routes ---
    # $connect
    create_route_and_integration("$connect", connect_arn)
    # $disconnect
    create_route_and_integration("$disconnect", disconnect_arn)
    # sendMessage
    create_route_and_integration("sendMessage", sendmessage_arn)

    # --- Step 3: Deploy the WebSocket API ---
    try:
        deployment = apigateway.create_deployment(
            ApiId=api_id,
            Description="Initial deployment"
        )
        stage = apigateway.create_stage(
            ApiId=api_id,
            StageName="dev",
            DeploymentId=deployment["DeploymentId"]
        )
        print(f"✅ WebSocket API deployed to stage 'dev'")
    except ClientError as e:
        print(f"❌ Failed to deploy WebSocket API: {e}")
        return None

    return {"api_id": api_id, "endpoint": api_endpoint}
