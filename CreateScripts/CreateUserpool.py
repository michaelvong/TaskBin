import boto3
import json
import os
import time

def setup_cognito(frontend_url, region="us-west-1"):
    cognito = boto3.client("cognito-idp", region_name=region)

    print("🔧 Creating Cognito User Pool...")

    # -----------------------------------------------------------
    # Create User Pool with email + name attributes
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
            {
                "Name": "email",
                "AttributeDataType": "String",
                "Mutable": False,
                "Required": True,
            },
            {
                "Name": "name",
                "AttributeDataType": "String",
                "Mutable": True,
                "Required": True,
            }
        ],
        AutoVerifiedAttributes=["email"]
    )

    user_pool_id = response["UserPool"]["Id"]
    print(f"✔ Created User Pool: {user_pool_id}")

    # -----------------------------------------------------------
    # Create App Client (no secret)
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

    app_client_id = app_client["UserPoolClient"]["ClientId"]
    print(f"✔ App Client ID: {app_client_id}")

    # -----------------------------------------------------------
    # Create Hosted UI domain
    # -----------------------------------------------------------
    domain_prefix = f"taskbin-demo-{int(time.time())}"
    cognito.create_user_pool_domain(
        Domain=domain_prefix,
        UserPoolId=user_pool_id,
    )

    print(f"✔ Hosted UI Domain: {domain_prefix}.auth.{region}.amazoncognito.com")

    # -----------------------------------------------------------
    # IMPORTANT: Cognito often ignores OAuth settings unless updated afterward
    # -----------------------------------------------------------
    print("🔁 Applying OAuth settings (Cognito quirk)...")
    time.sleep(1)  # REQUIRED — Cognito ignores initial settings without delay

    cognito.update_user_pool_client(
        UserPoolId=user_pool_id,
        ClientId=app_client_id,
        SupportedIdentityProviders=["COGNITO"],
        CallbackURLs=[frontend_url],
        LogoutURLs=[frontend_url],
        AllowedOAuthFlows=["implicit"],
        AllowedOAuthScopes=["email", "openid"],
        AllowedOAuthFlowsUserPoolClient=True
    )

    # -----------------------------------------------------------
    # Auto-create 2 demo users
    # -----------------------------------------------------------
    test_password = "Str0ngP@ssw0rd!"

    demo_users = [
        ("testuser@example.com", "Test User"),
        ("testuser2@example.com", "Test User Two"),
    ]

    for email, name in demo_users:
        print(f"👤 Creating demo user: {email}")

        # Create user with attributes
        cognito.admin_create_user(
            UserPoolId=user_pool_id,
            Username=email,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "email_verified", "Value": "true"},
                {"Name": "name", "Value": name}
            ],
            MessageAction="SUPPRESS",  # prevents sending invite email
        )

        # Set password + force confirm user
        cognito.admin_set_user_password(
            UserPoolId=user_pool_id,
            Username=email,
            Password=test_password,
            Permanent=True  # user doesn't need to reset password
        )

        print(f"   ✔ Created and confirmed {email}")

    # -----------------------------------------------------------
    # Hosted UI login URL (returned to BuildMain)
    # -----------------------------------------------------------
    hosted_ui_url = (
        f"https://{domain_prefix}.auth.{region}.amazoncognito.com/login"
        f"?client_id={app_client_id}"
        f"&response_type=token"
        f"&scope=email+openid"
        f"&redirect_uri={frontend_url}"
    )

    print("\n🔐 Login URL:")
    print(hosted_ui_url)

    return user_pool_id, app_client_id, domain_prefix, hosted_ui_url
