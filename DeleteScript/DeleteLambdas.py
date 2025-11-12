import boto3
from botocore.exceptions import ClientError

AWS_REGION = "us-west-1"
lambda_client = boto3.client("lambda", region_name=AWS_REGION)

# --- Define the names of all TaskBin CRUD Lambdas ---
LAMBDA_NAMES = [
    "BoardCreateLambda",
    "BoardReadLambda",
    "BoardUpdateLambda",
    "BoardDeleteLambda",
    "TaskCreateLambda",
    "TaskReadLambda",
    "TaskUpdateLambda",
    "TaskDeleteLambda"
]


def delete_lambda(function_name: str):
    """
    Deletes a single Lambda function by name.
    """
    try:
        lambda_client.delete_function(FunctionName=function_name)
        print(f"🗑️ Deleted Lambda: {function_name}")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            print(f"⚠️ Lambda {function_name} not found. Skipping.")
        else:
            raise e


def delete_all_lambdas():
    """
    Deletes all TaskBin CRUD Lambda functions.
    """
    print("🚨 Starting deletion of TaskBin Lambda functions...")
    for name in LAMBDA_NAMES:
        delete_lambda(name)
    print("✅ All deletable Lambdas processed.")


# --- Allow orchestrator to call directly ---
if __name__ == "__main__":
    delete_all_lambdas()
