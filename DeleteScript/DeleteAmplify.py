# delete_amplify_app.py
import boto3
import sys

def delete_amplify_app(app_name, region="us-west-1"):
    amplify = boto3.client("amplify", region_name=region)

    # Find the app by name
    apps = amplify.list_apps()["apps"]
    app = next((a for a in apps if a["name"] == app_name), None)

    if not app:
        print(f"No Amplify app found with name '{app_name}'")
        return

    app_id = app["appId"]
    print(f"Deleting Amplify app '{app_name}' (ID: {app_id})...")

    try:
        amplify.delete_app(appId=app_id)
        print(f"Amplify app '{app_name}' successfully deleted.")
    except Exception as e:
        print(f"Error deleting app: {e}")
        sys.exit(1)
