# TaskBin/DeleteScript/delete_lambdas.py

import json
import boto3
import os

def delete_lambdas(json_path=None, region='us-west-1'):
    """
    Delete all Lambda functions listed in a JSON file.

    Args:
        json_path (str): Path to lambda_arns.json. Defaults to '../CreateScripts/lambda_arns.json'.
        region (str): AWS region where Lambdas are located.
    """
    # Default path if not provided
    if not json_path:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        json_path = os.path.join(base_dir, 'CreateScripts', 'lambda_arns.json')

    # Load Lambda ARNs from JSON
    with open(json_path, 'r') as f:
        lambda_dict = json.load(f)

    # Create Lambda client
    lambda_client = boto3.client('lambda', region_name=region)

    # Delete Lambdas
    for name, arn in lambda_dict.items():
        try:
            function_name = arn.split(':')[-1]
            print(f"Deleting Lambda: {function_name}...")
            lambda_client.delete_function(FunctionName=function_name)
            print(f"✅ Deleted {function_name}")
        except Exception as e:
            print(f"❌ Failed to delete {name}: {e}")
