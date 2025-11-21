from TaskBin.DeleteScript.DeleteUserpool import delete_user_pool
from TaskBin.DeleteScript.DeleteDB import delete_table
from TaskBin.DeleteScript.DeleteAPI import delete_all_apis
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # DeleteScript folder
create_scripts_dir = os.path.join(BASE_DIR, "CreateScripts")
lambda_arns_file = os.path.join(create_scripts_dir, "lambda_arns.json")
lambda_arns_file = os.path.abspath(lambda_arns_file)
api_file = os.path.join(BASE_DIR, "..", "api_id.json")
api_file = os.path.abspath(api_file)

def main():
    delete_user_pool()
    success = delete_table()
    if success:
        print("DynamoDB table deletion complete.")
    else:
        print("DynamoDB table deletion failed.")

    results = delete_all_apis()
    print("API deletion results:", results)

    # ✅ Delete the Lambda ARNs file
    if os.path.exists(lambda_arns_file):
        os.remove(lambda_arns_file)
        print(f"✅ Deleted {lambda_arns_file}")
    else:
        print(f"⚠️ File not found, nothing to delete: {lambda_arns_file}")

if __name__ == "__main__":
    main()