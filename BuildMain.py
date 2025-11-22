from TaskBin.CreateScripts.CreateDB import create_table
from TaskBin.CreateScripts.CreateUserpool import setup_cognito
from TaskBin.CreateScripts.CreateLambdas import create_all_lambdas
from TaskBin.CreateScripts.CreateWebsocket import setup_websocket_api
from TaskBin.CreateScripts.CreateAPI import APIOrchestrator
from TaskBin.CreateScripts.DeployAmplify import deploy_frontend
import boto3
import time

def update_cognito_redirects(user_pool_id, client_id, frontend_url, region="us-west-1"):
    """
    After Amplify deploy, update Cognito callback URLs to use the real frontend URL.
    """
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


def main():
    print("=" * 30 + " Starting TaskBin AWS setup... " + "=" * 30)

    # ------------------------------------------------------------
    # 1. Initial Cognito Setup (temporary localhost redirect)
    # ------------------------------------------------------------
    print("=" * 30 + " Setting up Cognito (Initial) " + "=" * 30)

    # Use temporary localhost redirect until Amplify deploy finishes
    temp_frontend = "http://localhost:5173"

    user_pool_id, client_id, domain_prefix, hosted_ui_url = setup_cognito(temp_frontend)

    print("\n=== Temporary Cognito Login URL ===")
    print(hosted_ui_url)

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
    # 6. Deploy Frontend (requires API to exist already)
    # ------------------------------------------------------------
    print("=" * 30 + " Deploying Frontend " + "=" * 30)
    frontend_url = deploy_frontend()
    print("Amplify frontend URL:", frontend_url)

    # ------------------------------------------------------------
    # 7. Patch Cognito redirect URIs with real Amplify URL
    # ------------------------------------------------------------
    update_cognito_redirects(user_pool_id, client_id, frontend_url)

    # Build updated hosted UI URL
    region = "us-west-1"
    hosted_ui_url = (
        f"https://{domain_prefix}.auth.{region}.amazoncognito.com/login"
        f"?client_id={client_id}"
        f"&response_type=token"
        f"&scope=email+openid"
        f"&redirect_uri={frontend_url}"
    )

    print("=" * 30 + " TaskBin AWS Setup Complete" + "=" * 30)

    # ------------------------------------------------------------
    # FINAL DEBUG SUMMARY
    # ------------------------------------------------------------
    print("\n\n================= TASKBIN DEPLOY SUMMARY =================")
    print(f"API Endpoint: {api_base_url}")
    print(f"Hosted UI Login URL:\n{hosted_ui_url}")
    print("===========================================================\n")


if __name__ == "__main__":
    main()
