import boto3
import time

def delete_user_pool(pool_name="TaskBinUserPool", region="us-west-1"):
    cognito = boto3.client("cognito-idp", region_name=region)

    # -----------------------------------------------------
    # 1. Lookup the user pool ID
    # -----------------------------------------------------
    print("\n🔍 Looking up user pool...")

    try:
        pools = cognito.list_user_pools(MaxResults=60)["UserPools"]
        matches = [p for p in pools if p["Name"] == pool_name]

        if not matches:
            print("✔ User pool does not exist — nothing to delete.")
            return

        user_pool_id = matches[0]["Id"]
        print(f"✔ Found User Pool ID: {user_pool_id}")

    except Exception as e:
        print("❌ Error listing user pools:", e)
        return

    # -----------------------------------------------------
    # 2. Delete Hosted UI domain first
    # -----------------------------------------------------
    domain_prefix = pool_name.lower()
    print(f"\n🗑️ Attempting to delete Hosted UI domain: {domain_prefix}")

    try:
        cognito.delete_user_pool_domain(
            Domain=domain_prefix,
            UserPoolId=user_pool_id
        )
        print("✔ Domain deletion started")
    except cognito.exceptions.InvalidParameterException:
        print("ℹ Domain may not exist or already deleted — continuing...")
    except Exception as e:
        print("⚠️ Unexpected error deleting domain:", e)

    time.sleep(1)

    # -----------------------------------------------------
    # 3. Delete ALL App Clients
    # -----------------------------------------------------
    print("\n🗑️ Deleting app clients...")

    try:
        clients = cognito.list_user_pool_clients(UserPoolId=user_pool_id)["UserPoolClients"]
        if not clients:
            print("ℹ No app clients found.")
        else:
            for c in clients:
                cid = c["ClientId"]
                cname = c.get("ClientName", "(no-name)")
                print(f"  - Deleting client: {cname} ({cid})")
                try:
                    cognito.delete_user_pool_client(
                        UserPoolId=user_pool_id,
                        ClientId=cid
                    )
                except Exception as e:
                    print(f"    ⚠️ Error deleting client {cid}: {e}")

    except Exception as e:
        print("⚠️ Error listing app clients:", e)

    time.sleep(1)

    # -----------------------------------------------------
    # 4. Delete the User Pool (may require retries)
    # -----------------------------------------------------
    print(f"\n🗑️ Deleting User Pool: {user_pool_id}")

    for attempt in range(8):
        try:
            cognito.delete_user_pool(UserPoolId=user_pool_id)
            print("✔ User Pool deleted successfully!")
            return
        except cognito.exceptions.ResourceNotFoundException:
            print("✔ User Pool already gone.")
            return
        except cognito.exceptions.InvalidParameterException as e:
            # Happens if domain still detaching
            if "domain" in str(e).lower():
                print("⏳ Cognito still cleaning up domain… retrying...")
                time.sleep(3)
                continue
            else:
                print("❌ Other InvalidParameterException:", e)
                return
        except Exception as e:
            print("⚠️ Unexpected error during deletion:", e)
            return

    print("❌ Failed to delete user pool after multiple retries.")


if __name__ == "__main__":
    delete_user_pool()
