import os
import subprocess
import hashlib
import boto3
import requests
import sys
import shutil
import json

# -----------------------------
# Helper functions
# -----------------------------

def check_path(path, name):
    if not os.path.isdir(path):
        raise NotADirectoryError(f"{name} not found: {path}")

def run_command(cmd, cwd, env=None):
    """Run shell command, works on Windows/macOS"""
    print(f"[CMD] {cmd}")
    result = subprocess.run(cmd, cwd=cwd, shell=True, env=env)
    if result.returncode != 0:
        sys.exit(f"Command failed: {cmd}")

def detect_node_and_npm():
    """
    Detect Node.js and NPM manually and return full paths.
    """
    print("Detecting Node.js and npm...")

    # Try Windows standard install directory
    possible_node = r"C:\Program Files\nodejs\node.exe"
    possible_npm = r"C:\Program Files\nodejs\npm.cmd"

    if os.path.exists(possible_node) and os.path.exists(possible_npm):
        print(f"✔ Using Node from: {possible_node}")
        print(f"✔ Using NPM from : {possible_npm}")
        return possible_node, possible_npm

    # Try PATH search
    node_path = shutil.which("node")
    npm_path = shutil.which("npm")

    if node_path and npm_path:
        print(f"✔ Using Node from PATH: {node_path}")
        print(f"✔ Using NPM from PATH : {npm_path}")
        return node_path, npm_path

    # FAILURE
    print("❌ Node.js not found in PATH or standard install location.")
    sys.exit("Install Node.js 20.19+ or add to PATH and restart PyCharm.")

def md5_hash(file_path):
    """Compute MD5 hash for a file"""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def build_md5_file_map(source_dir):
    """Build fileMap with MD5 hashes for Amplify deployment"""
    file_map = {}
    for root, dirs, files in os.walk(source_dir):
        for fname in files:
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, start=source_dir).replace("\\", "/")
            file_map[rel_path] = md5_hash(full_path)
    return file_map

def get_frontend_url_temp(app_id, branch_name):
    """Return the temporary Amplify frontend URL immediately"""
    return f"https://{branch_name}.{app_id}.amplifyapp.com/"

# -----------------------------
# Main deploy function
# -----------------------------

def deploy_frontend(
        frontend_dir=None,
        app_name="TaskBinFrontend",
        branch_name="main",
        region="us-west-1"
):
    # Detect Node + npm
    node_path, npm_path = detect_node_and_npm()

    # Default frontend_dir relative to this script
    if frontend_dir is None:
        SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
        frontend_dir = os.path.join(SCRIPT_DIR, "..", "taskbin-frontend-complete")

    dist_dir = os.path.join(frontend_dir, "dist")

    # -----------------------------
    # Step 0a: Create .env.production dynamically
    # -----------------------------
    api_json_file = os.path.join(os.path.dirname(frontend_dir), "api_id.json")
    if not os.path.isfile(api_json_file):
        sys.exit(f"api_id.json not found at {api_json_file}")

    with open(api_json_file) as f:
        api_data = json.load(f)

    api_id = api_data.get("api_id")
    websocket_api_id = api_data.get("websocket_api_id")

    if not api_id or not websocket_api_id:
        sys.exit("api_id or websocket_api_id missing in api_id.json")

    # Assume stage is 'dev' for WebSocket
    stage = "dev"

    env_content = f"""
VITE_API_BASE_URL=https://{api_id}.execute-api.{region}.amazonaws.com/prod
VITE_WEBSOCKET_API_URL=wss://{websocket_api_id}.execute-api.{region}.amazonaws.com/{stage}
VITE_TEST_USER_ID=your-test-user-id
"""

    env_file = os.path.join(frontend_dir, ".env.production")
    with open(env_file, "w") as f:
        f.write(env_content.strip() + "\n")

    print(f"✅ .env.production file created/updated at {env_file}")

    # Step 0b: Check frontend folder
    check_path(frontend_dir, "Frontend folder")

    # Step 1: Build frontend in production mode
    print("Building Vite frontend in production mode...")

    # Use absolute paths for npm
    run_command(f'"{npm_path}" install', cwd=frontend_dir)
    run_command(f'"{npm_path}" run build -- --mode production', cwd=frontend_dir)

    # Ensure dist exists after build
    check_path(dist_dir, "dist folder")
    print("Build complete.")

    # Step 2: Initialize Amplify client
    amplify = boto3.client("amplify", region_name=region)

    # Step 3: Create or get Amplify app
    apps = amplify.list_apps()["apps"]
    app = next((a for a in apps if a["name"] == app_name), None)

    if not app:
        print(f"Creating Amplify app '{app_name}'...")
        response = amplify.create_app(
            name=app_name,
            repository="",
            platform="WEB"
        )
        app_id = response["app"]["appId"]
    else:
        print(f"Using existing Amplify app '{app_name}'")
        app_id = app["appId"]

    # Step 4: Create branch if needed
    branches = amplify.list_branches(appId=app_id)["branches"]
    branch = next((b for b in branches if b["branchName"] == branch_name), None)

    if not branch:
        print(f"Creating branch '{branch_name}'...")
        branch = amplify.create_branch(
            appId=app_id,
            branchName=branch_name
        )["branch"]
    else:
        print(f"Branch '{branch_name}' already exists")

    branch_name_actual = branch["branchName"]
    print(f"Branch ready: {branch_name_actual}")

    # Step 5: Prepare fileMap
    print("Building MD5 fileMap from dist/ folder...")
    file_map = build_md5_file_map(dist_dir)
    print(f"Total files to deploy: {len(file_map)}")

    # Step 6: Create deployment
    print("Creating deployment...")
    deployment = amplify.create_deployment(
        appId=app_id,
        branchName=branch_name_actual,
        fileMap=file_map
    )
    job_id = deployment["jobId"]
    upload_urls = deployment["fileUploadUrls"]
    print("Deployment created with jobId:", job_id)

    # Step 7: Upload files
    print("Uploading files...")
    for rel_path, url in upload_urls.items():
        full_path = os.path.join(dist_dir, rel_path.replace("/", os.sep))
        with open(full_path, "rb") as f:
            data = f.read()
        response = requests.put(url, data=data)
        response.raise_for_status()
    print("All files uploaded successfully.")

    # Step 8: Start deployment
    print("Starting deployment...")
    amplify.start_deployment(
        appId=app_id,
        branchName=branch_name_actual,
        jobId=job_id
    )

    # Step 9: Return frontend URL
    frontend_url = get_frontend_url_temp(app_id, branch_name_actual)
    print(f"Frontend is available at: {frontend_url}")

    return frontend_url
