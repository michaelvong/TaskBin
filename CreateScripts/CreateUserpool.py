import boto3
import time

def setup_cognito(region="us-west-1"):
    cognito = boto3.client("cognito-idp", region_name=region)

    print("🔧 Creating Cognito User Pool...")

    # -----------------------------------------------------------
    # Create User Pool
    # -----------------------------------------------------------
    response = cognito.create_user_pool(
        PoolName="TaskBinUserPool",
        Policies={
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireUppercase": False,
                "RequireLowercase": True,
                "RequireNumbers": False,
                "RequireSymbols": False,
            }
        },
        Schema=[
            {"Name": "email", "AttributeDataType": "String", "Mutable": False, "Required": True},
            {"Name": "name",  "AttributeDataType": "String", "Mutable": True,  "Required": True},
        ],
        AutoVerifiedAttributes=["email"]
    )

    user_pool_id = response["UserPool"]["Id"]
    print(f"✔ Created User Pool: {user_pool_id}")

    # -----------------------------------------------------------
    # Create App Client (temporary localhost redirect)
    # -----------------------------------------------------------
    app_client = cognito.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName="TaskBinAppClient",
        GenerateSecret=False,
        ExplicitAuthFlows=[
            "ALLOW_USER_PASSWORD_AUTH",
            "ALLOW_USER_SRP_AUTH",
        ],
        AllowedOAuthFlowsUserPoolClient=True,
        AllowedOAuthFlows=["implicit"],
        AllowedOAuthScopes=["email", "openid"],
        CallbackURLs=["http://localhost:5173"],
        LogoutURLs=["http://localhost:5173"]
    )

    client_id = app_client["UserPoolClient"]["ClientId"]
    print(f"✔ App Client ID: {client_id}")

    # -----------------------------------------------------------
    # Create Hosted UI Domain
    # -----------------------------------------------------------
    domain_prefix = f"taskbin-demo-{int(time.time())}"

    cognito.create_user_pool_domain(
        Domain=domain_prefix,
        UserPoolId=user_pool_id,
    )

    print(f"✔ Hosted UI Domain: {domain_prefix}.auth.{region}.amazoncognito.com")

    # -----------------------------------------------------------
    # Create demo users
    # -----------------------------------------------------------
    test_password = "Str0ngP@ssw0rd!"
    demo_users = [
        ("testuser@example.com",  "Test User"),
        ("testuser2@example.com", "Test User Two"),
    ]

    for email, name in demo_users:
        print(f"👤 Creating demo user: {email}")

        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "name", "Value": name}
            ],
            MessageAction="SUPPRESS",
        )

        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=test_password,
            Permanent=True
        )

        print(f"   ✔ Created and confirmed {email}")

    # -----------------------------------------------------------
    # Return IDs — NOT the login URL (will be generated later)
    # -----------------------------------------------------------
    return user_pool_id, client_id, domain_prefix
