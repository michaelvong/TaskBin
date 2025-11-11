import boto3
import time

def delete_table(
    table_name="TaskBin",
    region="us-west-1",
    max_retries=3,
    retry_delay=10
):
    """
    Deletes a DynamoDB table with retry logic.
    """
    dynamodb = boto3.client('dynamodb', region_name=region)

    for attempt in range(1, max_retries + 1):
        try:
            dynamodb.delete_table(TableName=table_name)
            print(f"Table '{table_name}' deletion initiated.")
            return True
        except dynamodb.exceptions.ResourceNotFoundException:
            print(f"Table '{table_name}' does not exist.")
            return True  # Consider this a "success"
        except Exception as e:
            print(f"Error deleting table '{table_name}': {e}")
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds... (Attempt {attempt}/{max_retries})")
                time.sleep(retry_delay)
                return None
            else:
                print(f"Failed to delete table '{table_name}' after {max_retries} attempts.")
                return False

    return True
