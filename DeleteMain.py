from TaskBin.DeleteScript.DeleteUserpool import delete_user_pool
from TaskBin.DeleteScript.DeleteDB import delete_table
from TaskBin.DeleteScript.DeleteAPI import delete_all_apis
from TaskBin.DeleteScript.DeleteAmplify import delete_amplify_app
from TaskBin.DeleteScript.DeleteLambdas import delete_lambdas
import os
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # DeleteScript folder
create_scripts_dir = os.path.join(BASE_DIR, "CreateScripts")
lambda_arns_file = os.path.abspath(os.path.join(create_scripts_dir, "lambda_arns.json"))
api_file = os.path.abspath(os.path.join(BASE_DIR, "..", "api_id.json"))

def main():

    # ------------------------------------------------------------
    # 0. Delete Amplify frontend FIRST (correct ordering)
    # ------------------------------------------------------------
    APP_NAME = "TaskBinFrontend"
    print(f"Deleting Amplify app '{APP_NAME}'...")
    delete_amplify_app(APP_NAME)
    print("✔ Amplify frontend deleted.\n")

    # ------------------------------------------------------------
    # 1. Delete Cognito User Pool
    # ------------------------------------------------------------
    delete_user_pool("TaskBinUserPool")

    # ------------------------------------------------------------
    # 2. Delete DynamoDB Table
    # ------------------------------------------------------------
    success = delete_table()
    if success:
        print("DynamoDB table deletion complete.")
    else:
        print("DynamoDB table deletion failed.")

    # ------------------------------------------------------------
    # 3. Delete ALL APIs (HTTP + WebSocket)
    # ------------------------------------------------------------
    results = delete_all_apis()
    print("API deletion results:", results)

    # ------------------------------------------------------------
    # 4. Delete Lambda ARNs file
    # ------------------------------------------------------------
    # print("Deleting Lambdas")
    # delete_lambdas()
    # if os.path.exists(lambda_arns_file):
    #     os.remove(lambda_arns_file)
    #     print(f"✔ Deleted {lambda_arns_file}")
    # else:
    #     print(f"⚠️ File not found, nothing to delete: {lambda_arns_file}")

if __name__ == "__main__":
    main()
