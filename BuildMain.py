from TaskBin.CreateScripts.CreateDB import create_table
from TaskBin.CreateScripts.CreateUserpool import setup_cognito
from TaskBin.CreateScripts.CreateLambdas import create_all_lambdas
from TaskBin.CreateScripts.CreateWebsocket import create_websocket_api
from TaskBin.CreateScripts.CreateAPI import create_all_apis
import time

def main():
    print("Starting TaskBin AWS setup...")
    setup_cognito()
    # 1. Create DynamoDB Table
    print("Creating DynamoDB table...")
    create_table()
    print("Creating Lambdas")
    ws_arns = create_all_lambdas()

    ws_api = create_websocket_api(
        ws_arns["connect_lambda_arn"],
        ws_arns["disconnect_lambda_arn"],
        ws_arns["sendmessage_lambda_arn"]
    )

    with open("websocket_api_id.txt", "w") as f:
        f.write(ws_api["api_id"])

    print(f"WebSocket API ID saved to websocket_api_id.txt for future deletion")
    api_info = create_all_apis()
    print("All API endpoints created:")
    for name, info in api_info.items():
        print(f"{name}: {info['endpoint']} (ID: {info['api_id']})")
    print("TaskBin AWS setup complete.")

if __name__ == "__main__":
    main()
