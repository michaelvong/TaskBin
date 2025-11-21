import boto3
import time

def setup_cognito(
    pool_name="TaskBinUserPool",
    test_username="testuser@example.com",
    test_password="Str0ngP@ssw0rd!",
    region="us-west-1",
    wait_retries=5,
    wait_delay=3,
    frontend_url="http://localhost:5173"
):
    """
    Sets up Cognito:
    - Creates user pool
    - Creates app client
    - Creates Hosted UI domain
    - Links app client to Hosted UI  (**this was missing**)
    - Enables OAuth2 implicit grant + scopes
    - Creates test user
    """

    cognito = boto3.client("cognito-idp", region_name=region)

    # ---------------------------------------------------------
    # 1. Create User Pool
    # ---------------------------------------------------------
    print("🔧 Creating user pool...")
    pool_resp = cognito.create_user_pool(
        PoolName=pool_name,
        AutoVerifiedAttributes=["email"],
        UsernameAttributes=["email"],
        Policies={
            "PasswordPolicy": {
                "MinimumLength": 8,
                "RequireLowercase": True,
                "RequireUppercase": True,
                "RequireNumbers": True,
                "RequireSymbols": True
            }
        }
    )
    user_pool_id = pool_resp["UserPool"]["Id"]
    print(f"✔ User Pool ID: {user_pool_id}")

    time.sleep(1)

    # ---------------------------------------------------------
    # 2. Create App Client (no client secret)
    # ---------------------------------------------------------
    print("🔧 Creating app client...")
    app_client_resp = cognito.create_user_pool_client(
        UserPoolId=user_pool_id,
        ClientName="TaskBinAppClient",
        GenerateSecret=False,
        ExplicitAuthFlows=["ALLOW_USER_PASSWORD_AUTH", "ALLOW_REFRESH_TOKEN_AUTH"],
        CallbackURLs=[frontend_url],
        LogoutURLs=[frontend_url],
        SupportedIdentityProviders=["COGNITO"],
        AllowedOAuthFlows=["implicit"],
        AllowedOAuthScopes=["email", "openid"],
        AllowedOAuthFlowsUserPoolClient=True
    )
    app_client_id = app_client_resp["UserPoolClient"]["ClientId"]
    print(f"✔ App Client ID: {app_client_id}")

    # IMPORTANT:
    # Cognito ignores some settings unless we UPDATE the client after creation.
    time.sleep(1)
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
    print("✔ App Client updated & linked to Hosted UI")

    # ---------------------------------------------------------
    # 3. Create Hosted UI domain
    # ---------------------------------------------------------
    domain_prefix = pool_name.lower()
    print(f"🔧 Creating domain '{domain_prefix}'...")
    try:
        cognito.create_user_pool_domain(
            Domain=domain_prefix,
            UserPoolId=user_pool_id
        )
        print("✔ Hosted UI domain created")
    except cognito.exceptions.InvalidParameterException as e:
        if "already exists" in str(e):
            print("ℹ Domain already exists, continuing...")
        else:
            raise

    hosted_ui_url = (
        f"https://{domain_prefix}.auth.{region}.amazoncognito.com/login"
        f"?client_id={app_client_id}"
        f"&response_type=token"
        f"&scope=email+openid"
        f"&redirect_uri={frontend_url}"
    )

    print(f"✔ Hosted UI URL:\n{hosted_ui_url}")

    # ---------------------------------------------------------
    # 4. Create & confirm test user
    # ---------------------------------------------------------
    print("🔧 Creating test user...")
    cognito.admin_create_user(
        UserPoolId=user_pool_id,
        Username=test_username,
        UserAttributes=[{"Name": "email", "Value": test_username}],
        MessageAction="SUPPRESS"
    )

    cognito.admin_set_user_password(
        UserPoolId=user_pool_id,
        Username=test_username,
        Password=test_password,
        Permanent=True
    )
    print(f"✔ Test user created: {test_username}")

    # ---------------------------------------------------------
    # Done
    # ---------------------------------------------------------
    return user_pool_id, app_client_id, domain_prefix, hosted_ui_url


if __name__ == "__main__":
    uid, cid, dom, url = setup_cognito()
    print("\n=== Cognito Setup Complete ===")
    print("User Pool ID:", uid)
    print("App Client ID:", cid)
    print("Domain Prefix:", dom)
    print("Hosted UI URL:", url)
