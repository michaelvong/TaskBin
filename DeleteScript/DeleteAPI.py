import os
import json
import boto3
from botocore.exceptions import ClientError

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))          # TaskBin/DeleteScripts
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, ".."))   # TaskBin/
CREATE_DIR = os.path.join(PROJECT_ROOT, "CreateScripts")       # TaskBin/CreateScripts
API_ID_FILE = os.path.join(PROJECT_ROOT, "api_id.json")        # TaskBin/api_id.json

# Boto3 client for API Gateway
apigatewayv2 = boto3.client("apigatewayv2", region_name="us-west-1")

def delete_all_apis():
    if not os.path.exists(API_ID_FILE):
        print("⚠️ No api_id.json found — nothing to delete.")
        return {"status": "no-api-id-file"}

    with open(API_ID_FILE, "r") as f:
        api_ids = json.load(f)

    if not api_ids:
        print("⚠️ api_id.json is empty — nothing to delete.")
        return {"status": "empty-api-id-file"}

    deletion_results = {}

    for name, api_id in api_ids.items():
        if not api_id:
            print(f"⚠️ No API ID for {name}, skipping...")
            deletion_results[name] = {"status": "missing-api-id"}
            continue

        print(f"🚀 Deleting API '{name}' with ID: {api_id}")
        try:
            apigatewayv2.delete_api(ApiId=api_id)
            deletion_results[name] = {"status": "deleted"}
            print(f"✅ API '{name}' deleted successfully")

        except ClientError as e:
            print(f"❌ Failed to delete API '{name}': {e}")
            deletion_results[name] = {"status": "error", "error": str(e)}

        except Exception as e:
            print(f"❌ Unexpected error deleting API '{name}': {e}")
            deletion_results[name] = {"status": "exception", "error": str(e)}

    # Remove api_id.json after all deletions
    try:
        os.remove(API_ID_FILE)
        print("🗑️ Deleted api_id.json")
    except Exception as e:
        print(f"❌ Failed to delete api_id.json: {e}")

    return deletion_results


if __name__ == "__main__":
    results = delete_all_apis()
    print("Deletion results:", results)
