import boto3
import time

def delete_user_pool(pool_name="TaskBinUserPool", region="us-west-1", max_retries=3, retry_delay=10):
    """
    Deletes a Cognito User Pool by name.
    Retries up to max_retries if deletion fails.
    """
    client = boto3.client("cognito-idp", region_name=region)

    # Helper: get pool ID by name
    def get_user_pool_id():
        pools = client.list_user_pools(MaxResults=60)['UserPools']
        for p in pools:
            if p['Name'] == pool_name:
                return p['Id']
        return None

    for attempt in range(1, max_retries + 1):
        try:
            user_pool_id = get_user_pool_id()
            if not user_pool_id:
                print(f"User Pool '{pool_name}' does not exist.")
                return

            client.delete_user_pool(UserPoolId=user_pool_id)
            print(f"User Pool '{pool_name}' deletion initiated.")
            return

        except Exception as e:
            print(f"Error deleting User Pool '{pool_name}': {e}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds... (Attempt {attempt}/{max_retries})")
                time.sleep(retry_delay)
            else:
                raise Exception(f"Failed to delete User Pool '{pool_name}' after {max_retries} attempts.")
