import os
import importlib.util
import json

# Folder containing your individual API scripts
APIS_DIR = os.path.join(os.path.dirname(__file__), "APIs")
API_ID_FILE = os.path.join(os.path.dirname(__file__), "api_ids.json")


def create_all_apis():
    """
    Dynamically loads all Python scripts in the APIS_DIR and calls their
    create_api() function. Saves all API IDs and endpoints to a JSON file.
    Returns a dictionary of API info.
    """
    if not os.path.exists(APIS_DIR):
        print(f"❌ APIs directory not found: {APIS_DIR}")
        return {}

    api_files = [f for f in os.listdir(APIS_DIR) if f.endswith(".py")]
    if not api_files:
        print("⚠️ No API scripts found.")
        return {}

    api_info_dict = {}

    for file_name in api_files:
        file_path = os.path.join(APIS_DIR, file_name)
        module_name = file_name.replace(".py", "")

        print(f"📦 Loading API script: {file_name}")

        spec = importlib.util.spec_from_file_location(module_name, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "create_api") and callable(module.create_api):
            print(f"🚀 Creating API from script: {module_name}")
            try:
                api_info = module.create_api()  # Each script returns {"api_id":..., "endpoint":...}
                api_info_dict[module_name] = api_info
                print(f"✅ API created: {api_info}")
            except Exception as e:
                print(f"❌ Failed to create API from {module_name}: {e}")
        else:
            print(f"⚠️ Script {module_name} does not have a callable create_api() function")

    # Save API IDs and endpoints for future reference (deletion, orchestration)
    with open(API_ID_FILE, "w") as f:
        json.dump(api_info_dict, f, indent=2)

    print("✅ All APIs created successfully.")
    return api_info_dict


if __name__ == "__main__":
    apis = create_all_apis()
    print("All API info:", apis)
