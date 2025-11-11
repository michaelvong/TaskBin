import boto3
import time

def setup_cognito(
    pool_name="TaskBinUserPool",
    test_username="testuser@example.com",
    test_password="Str0ngP@ssw0rd!",
    region="us-west-1",
    wait_retries=5,
    wait_delay=3
):
    """
    Sets up Cognito for TaskBin:
    1. Creates a user pool
    2. Waits until the pool is active
    3. Creates an app client
    4. Creates a test user
    5. Confirms the test user

    Returns:
        user_pool_id, app_client_id
    """
    client = boto3.client("cognito-idp", region_name=region)

    # -----------------------------
    # Step 1: Create User Pool
    # -----------------------------
    try:
        response = client.create_user_pool(
            PoolName=pool_name,
            AutoVerifiedAttributes=["email"],
            UsernameAttributes=["email"],
            Schema=[{"Name": "email", "AttributeDataType": "String", "Required": True}]
        )
        user_pool_id = response['UserPool']['Id']
        print(f"User Pool '{pool_name}' created with ID: {user_pool_id}")
    except client.exceptions.ResourceConflictException:
        # Pool already exists
        pools = client.list_user_pools(MaxResults=60)['UserPools']
        matching = [p for p in pools if p['Name'] == pool_name]
        if not matching:
            raise Exception(f"User Pool '{pool_name}' exists but could not be retrieved.")
        user_pool_id = matching[0]['Id']
        print(f"User Pool '{pool_name}' already exists with ID: {user_pool_id}")
    except Exception as e:
        raise Exception(f"Error creating user pool: {e}")

    # -----------------------------
    # Step 2: Wait for User Pool to be active
    # -----------------------------
    for attempt in range(wait_retries):
        try:
            client.describe_user_pool(UserPoolId=user_pool_id)
            print(f"User Pool '{user_pool_id}' is active.")
            break
        except client.exceptions.ResourceNotFoundException:
            print(f"Waiting for User Pool to become active... (Attempt {attempt + 1}/{wait_retries})")
            time.sleep(wait_delay)
    else:
        raise Exception(f"User Pool '{user_pool_id}' did not become active in time.")

    # -----------------------------
    # Step 3: Create App Client
    # -----------------------------
    try:
        response = client.create_user_pool_client(
            UserPoolId=user_pool_id,
            ClientName=f"{pool_name}AppClient",
            GenerateSecret=False,
            ExplicitAuthFlows=["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"]
        )
        app_client_id = response['UserPoolClient']['ClientId']
        print(f"App Client created with ID: {app_client_id}")
    except client.exceptions.ResourceConflictException:
        # App client already exists
        clients = client.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=60)['UserPoolClients']
        app_client_id = next((c['ClientId'] for c in clients if c['ClientName'] == f"{pool_name}AppClient"), None)
        if not app_client_id:
            raise Exception("App Client exists but could not be retrieved.")
        print(f"App Client already exists with ID: {app_client_id}")
    except Exception as e:
        raise Exception(f"Error creating App Client: {e}")

    # -----------------------------
    # Step 4: Create Test User
    # -----------------------------
    try:
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=test_username,
            UserAttributes=[
                {"Name": "email", "Value": test_username},
                {"Name": "email_verified", "Value": "True"}
            ],
            TemporaryPassword=test_password,
            MessageAction="SUPPRESS"
        )
        print(f"Test user '{test_username}' created.")
    except client.exceptions.UsernameExistsException:
        print(f"Test user '{test_username}' already exists.")
    except Exception as e:
        raise Exception(f"Error creating test user: {e}")

    # -----------------------------
    # Step 5: Confirm Test User
    # -----------------------------
    try:
        client.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=test_username,
            Password=test_password,
            Permanent=True
        )
        print(f"Test user '{test_username}' confirmed and password set permanently.")
    except Exception as e:
        raise Exception(f"Error confirming test user: {e}")

    return user_pool_id, app_client_id
