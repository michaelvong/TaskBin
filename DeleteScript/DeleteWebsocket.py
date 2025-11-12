import boto3
from botocore.exceptions import ClientError

REGION = "us-west-1"  # Update to your region
apigateway = boto3.client("apigatewayv2", region_name=REGION)

def delete_websocket_api(api_id):
    """
    Deletes a WebSocket API given its API ID.
    """
    try:
        # Delete the WebSocket API
        apigateway.delete_api(ApiId=api_id)
        print(f"✅ WebSocket API {api_id} deleted successfully.")
        return True
    except ClientError as e:
        print(f"❌ Failed to delete WebSocket API {api_id}: {e}")
        return False


# Example usage:
if __name__ == "__main__":
    # Replace with your actual WebSocket API ID
    api_id_to_delete = "abcd1234ef"
    delete_websocket_api(api_id_to_delete)
