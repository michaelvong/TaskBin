from TaskBin.DeleteScript.DeleteUserpool import delete_user_pool
from TaskBin.DeleteScript.DeleteDB import delete_table
from TaskBin.DeleteScript.DeleteWebsocket import delete_websocket_api
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

    #try:
        #with open("websocket_api_id.txt", "r") as f:
            #api_id_to_delete = f.read().strip()
    #except FileNotFoundError:
        #print("❌ websocket_api_id.txt not found. Cannot delete WebSocket API.")
        #exit(1)
    #deleted = delete_websocket_api(api_id_to_delete)
    #if deleted:
        # Optionally remove the file after successful deletion
        #os.remove("websocket_api_id.txt")
        #print("Deleted WebSocket API ID file.")

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