from TaskBin.CreateScripts.CreateDB import create_table
from TaskBin.CreateScripts.CreateUserpool import setup_cognito
from TaskBin.CreateScripts.CreateLambdas import create_all_lambdas
from TaskBin.CreateScripts.CreateWebsocket import setup_websocket_api
from TaskBin.CreateScripts.CreateAPI import APIOrchestrator
from TaskBin.CreateScripts.DeployAmplify import deploy_frontend
import time

def main():
    print("=" * 30 + " Starting TaskBin AWS setup... " + "=" * 30)

    # 1. Setup Cognito (User Pool, App Client, Domain)
    user_pool_id, client_id, domain_prefix, hosted_ui_url = setup_cognito()
    print("\n=== Cognito Login URL ===")
    print(hosted_ui_url)

    # 2. Create DynamoDB Table
    print("=" * 30 + " Creating DynamoDB table..." + "=" * 30)
    create_table()

    # 3. Create Lambdas
    print("=" * 30 + " Creating Lambdas " + "=" * 30)
    create_all_lambdas()

    # 4. Create API Gateway HTTP API
    print("=" * 30 + " Creating HTTP API " + "=" * 30)
    api_orchestrator = APIOrchestrator()
    api_id = api_orchestrator.get_or_create_api()
    api_orchestrator.create_all_routes()
    api_orchestrator.deploy_api()
    api_base_url = api_orchestrator.get_api_base_url()


    # 5. Create Websocket API
    print("=" * 30 + " Creating Websocket API " + "=" * 30)
    setup_websocket_api()
    # Call the deploy function
    print("=" * 30 + " Deploying Frontend" + "=" * 30)
    frontend_url = deploy_frontend()
    print("Amplify frontend URL:", frontend_url)
    print("=" * 30 + " TaskBin AWS Setup Complete" + "=" * 30)

    # 6. Print Hosted UI Login URL
    region = "us-west-1"
    login_url = (
        f"https://{domain_prefix}.auth.{region}.amazoncognito.com/login"
        f"?client_id={client_id}"
        f"&response_type=token"
        f"&scope=email+openid"
        f"&redirect_uri=http://localhost:5173"
    )

    print("\n=== Cognito Hosted UI Login URL ===")
    print(login_url)

    print("=" * 30 + " TaskBin AWS Setup Complete " + "=" * 30)

    # ------------------------------------------------------------
    # FINAL DEBUG SUMMARY
    # ------------------------------------------------------------
    print("\n\n================= TASKBIN DEPLOY SUMMARY =================")
    print(f"API Endpoint: {api_base_url}")              # from orchestrator
    print(f"Hosted UI Login URL:\n{login_url}")
    print("===========================================================\n")


if __name__ == "__main__":
    main()
