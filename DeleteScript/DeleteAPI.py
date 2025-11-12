import os
import importlib.util
import json

# Folder containing your individual API scripts
BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # DeleteScript folder
create_scripts_dir = os.path.join(BASE_DIR, "..", "CreateScripts")
api_file = os.path.join(create_scripts_dir, "api_ids.json")
API_ID_FILE = os.path.abspath(api_file)
APIS_DIR = os.path.join(create_scripts_dir, "APIs")


def delete_all_apis():
    """
    Dynamically loads all Python scripts in the APIS_DIR and calls their
    delete_api() function. Reads API IDs from the saved JSON file if needed.
    Also deletes the api_ids.json file at the end.
    Returns a dictionary of deletion results.
    """
    if not os.path.exists(APIS_DIR):
        print(f"❌ APIs directory not found: {APIS_DIR}")
        return {}

    # Try to load saved API IDs from previous creation
    api_ids = {}
    if os.path.exists(API_ID_FILE):
        with open(API_ID_FILE, "r") as f:
            api_ids = json.load(f)

    api_files = [f for f in os.listdir(APIS_DIR) if f.endswith(".py")]
    if not api_files:
        print("⚠️ No API scripts found.")
        return {}

    deletion_results = {}

    for file_name in api_files:
        file_path = os.path.join(APIS_DIR, file_name)
        module_name = file_name.replace(".py", "")

        print(f"📦 Loading API script: {file_name}")

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "delete_api") and callable(module.delete_api):
            print(f"🚀 Deleting API from script: {module_name}")
            try:
                # Pass API ID if available
                api_info = api_ids.get(module_name, {})
                api_id = api_info.get("api_id")
                result = module.delete_api(api_id=api_id)
                deletion_results[module_name] = result
                print(f"✅ API deleted: {module_name}")
            except Exception as e:
                print(f"❌ Failed to delete API from {module_name}: {e}")
        else:
            print(f"⚠️ Script {module_name} does not have a callable delete_api() function")

    # Delete the api_ids.json file after all APIs have been attempted
    if os.path.exists(API_ID_FILE):
        try:
            os.remove(API_ID_FILE)
            print(f"🗑️ Deleted API ID file: {API_ID_FILE}")
        except Exception as e:
            print(f"❌ Failed to delete API ID file: {e}")

    print("✅ All API deletions attempted.")
    return deletion_results


if __name__ == "__main__":
    results = delete_all_apis()
    print("Deletion results:", results)
