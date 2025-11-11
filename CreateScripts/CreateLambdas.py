import boto3
import os
import zipfile
import io
import time
import os
from botocore.exceptions import ClientError

# --- Configuration ---
LAMBDA_ROLE_ARN = "arn:aws:iam::508480286587:role/Lambda_TaskBin_Perms"  # <-- Update (MUST UPDATE TO UR OWN LAMBDA PERMS)
LAMBDA_RUNTIME = "python3.13"
LAMBDA_HANDLER = "lambda_function.lambda_handler"
REGION = "us-west-1"  # <-- Update if needed
BASE_DIR = os.path.dirname(__file__)
LAMBDA_DIR = os.path.join(BASE_DIR, "Lambdas")  # Folder containing your Lambda .py files
TIMEOUT = 30
MEMORY = 128

lambda_client = boto3.client("lambda", region_name=REGION)


def _zip_lambda_function(file_path: str) -> bytes:
    """Zips a single Lambda file in-memory for upload."""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(file_path, arcname="lambda_function.py")
    zip_buffer.seek(0)
    return zip_buffer.read()


def _generate_lambda_name(file_name: str) -> str:
    """Converts file name (e.g. board_create.py) → BoardCreateLambda"""
    base = file_name.replace(".py", "")
    parts = base.split("_")
    camel_case = "".join(p.capitalize() for p in parts)
    return f"TaskBin_{camel_case}"


def _create_or_update_lambda(lambda_name: str, zip_bytes: bytes):
    """Creates a new Lambda or updates an existing one."""
    try:
        print(f"🟢 Creating Lambda: {lambda_name}")
        lambda_client.create_function(
            FunctionName=lambda_name,
            Runtime=LAMBDA_RUNTIME,
            Role=LAMBDA_ROLE_ARN,
            Handler=LAMBDA_HANDLER,
            Code={"ZipFile": zip_bytes},
            Timeout=TIMEOUT,
            MemorySize=MEMORY,
            Publish=True,
        )
        print(f"✅ Created Lambda: {lambda_name}")

    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceConflictException":
            print(f"🟡 Updating existing Lambda: {lambda_name}")
            lambda_client.update_function_code(
                FunctionName=lambda_name,
                ZipFile=zip_bytes,
                Publish=True,
            )
            print(f"✅ Updated Lambda: {lambda_name}")
        else:
            print(f"❌ Failed for {lambda_name}: {e}")
            raise e


def create_all_lambdas():
    """
    Scans the lambdas folder and creates/updates all Lambda functions.
    Can be safely called from a main orchestrator script.
    """
    print("🚀 Starting Lambda build process...")

    if not os.path.exists(LAMBDA_DIR):
        print(f"❌ Lambdas directory not found: {LAMBDA_DIR}")
        return

    py_files = [f for f in os.listdir(LAMBDA_DIR) if f.endswith(".py")]
    if not py_files:
        print("⚠️ No Lambda files found.")
        return

    for file_name in py_files:
        file_path = os.path.join(LAMBDA_DIR, file_name)
        lambda_name = _generate_lambda_name(file_name)
        print(f"📦 Packaging {file_name} -> {lambda_name}")
        zip_bytes = _zip_lambda_function(file_path)
        _create_or_update_lambda(lambda_name, zip_bytes)
        time.sleep(1)

    print("✅ All Lambdas deployed successfully.")
