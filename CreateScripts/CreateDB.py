import boto3
import time

def create_table(table_name="TaskBin", region="us-west-1", max_retries=3, retry_delay=10):
    dynamodb = boto3.client('dynamodb', region_name=region)

    def _create():
        try:
            response = dynamodb.create_table(
                TableName=table_name,
                AttributeDefinitions=[
                    {"AttributeName": "PK", "AttributeType": "S"},
                    {"AttributeName": "SK", "AttributeType": "S"},
                    {"AttributeName": "GSI1PK", "AttributeType": "S"},
                    {"AttributeName": "GSI1SK", "AttributeType": "S"}
                ],
                KeySchema=[
                    {"AttributeName": "PK", "KeyType": "HASH"},
                    {"AttributeName": "SK", "KeyType": "RANGE"}
                ],
                BillingMode='PAY_PER_REQUEST',
                GlobalSecondaryIndexes=[
                    {
                        "IndexName": "GSI1",
                        "KeySchema": [
                            {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                            {"AttributeName": "GSI1SK", "KeyType": "RANGE"}
                        ],
                        "Projection": {"ProjectionType": "ALL"}
                    }
                ]
            )
            print(f"Table '{table_name}' creation initiated.")
            return True
        except dynamodb.exceptions.ResourceInUseException:
            print(f"Table '{table_name}' already exists.")
            return True
        except Exception as e:
            print(f"Error creating table: {e}")
            return False

    # Retry loop
    for attempt in range(1, max_retries + 1):
        success = _create()
        if success:
            break
        elif attempt < max_retries:
            print(f"Retrying table creation in {retry_delay} seconds... (Attempt {attempt}/{max_retries})")
            time.sleep(retry_delay)
        else:
            print(f"Failed to create table '{table_name}' after {max_retries} attempts.")
            raise Exception(f"Failed to create table '{table_name}'")
