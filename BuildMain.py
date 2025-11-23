from TaskBin.CreateScripts.CreateDB import create_table
from TaskBin.CreateScripts.CreateUserpool import setup_cognito
from TaskBin.CreateScripts.CreateLambdas import create_all_lambdas
from TaskBin.CreateScripts.CreateWebsocket import setup_websocket_api
from TaskBin.CreateScripts.CreateAPI import APIOrchestrator
from TaskBin.CreateScripts.DeployAmplify import deploy_frontend
import boto3
import time
import os
import uuid
from datetime import datetime, UTC


def update_cognito_redirects(user_pool_id, client_id, frontend_url, region="us-west-1"):
    cognito = boto3.client("cognito-idp", region_name=region)
    print("🔁 Updating Cognito callback URLs with real frontend URL...")

    cognito.update_user_pool_client(
        UserPoolId=user_pool_id,
        ClientId=client_id,
        SupportedIdentityProviders=["COGNITO"],
        CallbackURLs=[frontend_url],
        LogoutURLs=[frontend_url],
        AllowedOAuthFlows=["implicit"],
        AllowedOAuthScopes=["email", "openid"],
        AllowedOAuthFlowsUserPoolClient=True
    )

    print("✔ Cognito redirect URLs updated.")

def create_dummy_board():
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table("TaskBin")

    dummy_user_id = "testuser@example.com"
    board_id = str(uuid.uuid4())
    now = datetime.now(UTC).isoformat()

    print("🧪 Inserting dummy board into DynamoDB...")

    # Board metadata
    metadata = {
        "PK": f"BOARD#{board_id}",
        "SK": "METADATA",
        "type": "board",
        "board_id": board_id,
        "board_name": "Dummy Board",
        "description": "Automatically inserted during TaskBin setup.",
        "created_at": now,
        "owner_id": dummy_user_id,
    }

    # Membership row so it shows up in listBoards
    membership = {
        "PK": f"USER#{dummy_user_id}",
        "SK": f"BOARD#{board_id}",
        "type": "membership",
        "board_id": board_id,
        "user_id": dummy_user_id,
        "role": "owner",
        "joined_at": now,
    }

    table.put_item(Item=metadata)
    table.put_item(Item=membership)

    print("✔ Dummy board created!")

def main():
    print("=" * 30 + " Starting TaskBin AWS setup... " + "=" * 30)

    # ------------------------------------------------------------
    # 1. Initial Cognito Setup (temp localhost redirect)
    # ------------------------------------------------------------
    print("=" * 30 + " Setting up Cognito (Initial) " + "=" * 30)
    temp_frontend = "http://localhost:5173"
    user_pool_id, client_id, domain_prefix = setup_cognito()

    # ------------------------------------------------------------
    # 2. Create DynamoDB Table
    # ------------------------------------------------------------
    print("=" * 30 + " Creating DynamoDB table..." + "=" * 30)
    create_table()


    # ------------------------------------------------------------
    # 3. Create Lambdas
    # ------------------------------------------------------------
    print("=" * 30 + " Creating Lambdas " + "=" * 30)
    create_all_lambdas()

    # ------------------------------------------------------------
    # 4. Create API Gateway HTTP API (needed before Amplify)
    # ------------------------------------------------------------
    print("=" * 30 + " Creating HTTP API " + "=" * 30)
    api_orchestrator = APIOrchestrator()
    api_id = api_orchestrator.get_or_create_api()
    api_orchestrator.create_all_routes()
    api_orchestrator.deploy_api()
    api_base_url = api_orchestrator.get_api_base_url()

    # ------------------------------------------------------------
    # 5. Create Websocket API
    # ------------------------------------------------------------
    print("=" * 30 + " Creating Websocket API " + "=" * 30)
    setup_websocket_api()

    # ------------------------------------------------------------
    # 6. First Frontend Deploy (just to get URL)
    # ------------------------------------------------------------
    print("=" * 30 + " Deploying Frontend (initial) " + "=" * 30)
    frontend_url = deploy_frontend()
    print("Amplify frontend URL:", frontend_url)

    # ------------------------------------------------------------
    # 7. Construct final Hosted UI Login URL
    # ------------------------------------------------------------
    region = "us-west-1"
    hosted_ui_url = (
        f"https://{domain_prefix}.auth.{region}.amazoncognito.com/login"
        f"?client_id={client_id}"
        f"&response_type=token"
        f"&scope=email+openid"
        f"&redirect_uri={frontend_url}"
    )

    # ------------------------------------------------------------
    # 8. Update Cognito redirect URIs to real frontend
    # ------------------------------------------------------------
    update_cognito_redirects(user_pool_id, client_id, frontend_url)

    print("⏳ Waiting for Amplify to finish initial deployment...")
    time.sleep(10)

    # ------------------------------------------------------------
    # 9. Re-deploy Frontend with correct Hosted UI login URL in .env
    # ------------------------------------------------------------
    print("=" * 30 + " Re-deploying Frontend (with login URL) " + "=" * 30)
    deploy_frontend(hosted_ui_url=hosted_ui_url)

    # ------------------------------------------------------------
    # 2B. Insert Dummy Board
    # ------------------------------------------------------------
    create_dummy_board()

    # ------------------------------------------------------------
    # FINAL DEBUG SUMMARY
    # ------------------------------------------------------------
    print("\n\n================= TASKBIN DEPLOY SUMMARY =================")
    print(f"API Endpoint: {api_base_url}")
    print(f"Hosted UI Login URL:\n{hosted_ui_url}")
    print("===========================================================\n")

if __name__ == "__main__":
    main()
