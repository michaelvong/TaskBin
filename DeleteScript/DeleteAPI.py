import os
import importlib.util
import json

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))        # DeleteScripts/
CREATE_DIR = os.path.join(BASE_DIR, "..", "CreateScripts")   # CreateScripts/
API_ID_FILE = os.path.join(CREATE_DIR, "api_ids.json")
APIS_DIR = os.path.join(CREATE_DIR, "APIs")


def delete_all_apis():
    """
    Deletes all APIs listed in api_ids.json.
    Each key in api_ids.json should correspond to an API script in APIS_DIR.
    Calls delete_api(api_id=...) on each script, then removes api_ids.json.
    """
    if not os.path.exists(API_ID_FILE):
        print("⚠️ No api_ids.json found — nothing to delete.")
        return {"status": "no-api-id-file"}

    # Load all API IDs
    with open(API_ID_FILE, "r") as f:
        api_ids = json.load(f)

    if not api_ids:
        print("⚠️ api_ids.json is empty — nothing to delete.")
        return {"status": "empty-api-id-file"}

    deletion_results = {}

    for module_name, info in api_ids.items():
        api_id = info.get("api_id")
        if not api_id:
            print(f"⚠️ No api_id found for {module_name}, skipping...")
            deletion_results[module_name] = {"status": "missing-api-id"}
            continue

        # Locate API script
        api_script_path = os.path.join(APIS_DIR, f"{module_name}.py")
        if not os.path.exists(api_script_path):
            print(f"❌ API script not found for {module_name}: {api_script_path}")
            deletion_results[module_name] = {"status": "api-script-not-found"}
            continue

        # Load module dynamically
        spec = importlib.util.spec_from_file_location(module_name, api_script_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if not hasattr(module, "delete_api"):
            print(f"❌ {module_name}.py does NOT contain delete_api()")
            deletion_results[module_name] = {"status": "delete-function-not-found"}
            continue

        # Call delete_api()
        print(f"🚀 Deleting API {module_name} (id: {api_id})")
        try:
            result = module.delete_api(api_id=api_id)
            deletion_results[module_name] = {"status": "deleted", "result": result}
            print(f"✅ API {module_name} deleted successfully")
        except Exception as e:
            print(f"❌ Failed to delete {module_name}: {e}")
            deletion_results[module_name] = {"status": "exception", "error": str(e)}

    # Remove api_ids.json after all deletions
    try:
        os.remove(API_ID_FILE)
        print("🗑️ Deleted api_ids.json")
    except Exception as e:
        print(f"❌ Failed to delete api_ids.json: {e}")

    return deletion_results


if __name__ == "__main__":
    results = delete_all_apis()
    print("Deletion results:", results)
