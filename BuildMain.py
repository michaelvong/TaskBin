from TaskBin.CreateScripts.CreateDB import create_table
from TaskBin.CreateScripts.CreateUserpool import setup_cognito
from TaskBin.CreateScripts.CreateLambdas import create_all_lambdas
from CreateScripts.CreateWebsocket import setup_websocket_api
from TaskBin.CreateScripts.CreateAPI import APIOrchestrator
from TaskBin.CreateScripts.DeployAmplify import deploy_frontend
import time


def main():
    print("=" * 30 + " Starting TaskBin AWS setup... " + "=" * 30)
    setup_cognito()
    # 1. Create DynamoDB Table
    print("=" * 30 + " Creating DynamoDB table..." + "=" * 30)
    create_table()
    print("=" * 30 + " Creating Lambdas" + "=" * 30)
    create_all_lambdas()
    print("=" * 30 + " Creating API" + "=" * 30)
    api_orchestrator = APIOrchestrator()
    api_id = api_orchestrator.get_or_create_api()
    api_orchestrator.create_all_routes()
    api_orchestrator.deploy_api()
    print("=" * 30 + " Creating Websocket API" + "=" * 30)
    setup_websocket_api()
    # Call the deploy function
    print("=" * 30 + " Deploying Frontend" + "=" * 30)
    frontend_url = deploy_frontend()
    print("Amplify frontend URL:", frontend_url)
    print("=" * 30 + " TaskBin AWS Setup Complete" + "=" * 30)

if __name__ == "__main__":
    main()
