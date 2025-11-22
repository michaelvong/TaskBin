import boto3
import time

def delete_user_pool(pool_name="TaskBinUserPool", region="us-west-1"):
    cognito = boto3.client("cognito-idp", region_name=region)

    # -----------------------------------------------------
    # 1. Lookup the user pool ID
    # -----------------------------------------------------
    print("\n🔍 Looking up user pool...")

    pools = cognito.list_user_pools(MaxResults=60)["UserPools"]
    matches = [p for p in pools if p["Name"] == pool_name]

    if not matches:
        print("✔ User pool not found — nothing to delete.")
        return

    user_pool_id = matches[0]["Id"]
    print(f"✔ Found User Pool ID: {user_pool_id}")

    # -----------------------------------------------------
    # 2. Get domain + app clients
    # -----------------------------------------------------
    desc = cognito.describe_user_pool(UserPoolId=user_pool_id)["UserPool"]
    domain_prefix = desc.get("Domain")  # Full domain prefix
    print(f"🌐 User Pool Domain: {domain_prefix}")

    clients = cognito.list_user_pool_clients(UserPoolId=user_pool_id, MaxResults=60)["UserPoolClients"]
    client_ids = [c["ClientId"] for c in clients]

    # -----------------------------------------------------
    # 3. Delete domain first (CRITICAL)
    # -----------------------------------------------------
    if domain_prefix:
        print(f"🗑️ Deleting Hosted UI domain: {domain_prefix}")
        try:
            cognito.delete_user_pool_domain(
                Domain=domain_prefix,
                UserPoolId=user_pool_id
            )
            print("✔ Hosted UI domain deleted")
        except Exception as e:
            print(f"⚠️ Failed to delete domain (may already be deleted): {e}")

        # AWS needs propagation time
        time.sleep(3)

    # -----------------------------------------------------
    # 4. Delete all app clients
    # -----------------------------------------------------
    print("🗑️ Deleting app clients...")
    for cid in client_ids:
        try:
            cognito.delete_user_pool_client(UserPoolId=user_pool_id, ClientId=cid)
            print(f"✔ Deleted app client {cid}")
        except Exception as e:
            print(f"⚠️ Could not delete client {cid}: {e}")

    # -----------------------------------------------------
    # 5. Try deleting the user pool
    # -----------------------------------------------------
    print("🗑️ Deleting user pool...")

    for attempt in range(5):
        try:
            cognito.delete_user_pool(UserPoolId=user_pool_id)
            print("✔ User pool deleted successfully")
            return
        except cognito.exceptions.InvalidParameterException as e:
            msg = str(e)
            if "Custom domain" in msg or "domain" in msg:
                print("⏳ Domain still pending removal. Retrying in 2s...")
                time.sleep(2)
                continue
            else:
                print("❌ Unexpected InvalidParameterException:", e)
                return
        except Exception as e:
            print("⚠️ Unexpected error:", e)
            return

    print("❌ Failed to delete user pool after retries.")


if __name__ == "__main__":
    delete_user_pool()
