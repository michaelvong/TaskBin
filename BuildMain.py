from TaskBin.CreateScripts.CreateDB import create_table
from TaskBin.CreateScripts.CreateUserpool import setup_cognito
from TaskBin.CreateScripts.CreateLambdas import create_all_lambdas
import time

def main():
    print("Starting TaskBin AWS setup...")
    setup_cognito()
    # 1. Create DynamoDB Table
    print("Creating DynamoDB table...")
    create_table()
    print("Creating Lambdas")
    create_all_lambdas()
    # 2. Wait a few seconds to ensure table is active
    time.sleep(5)

    print("TaskBin AWS setup complete.")

if __name__ == "__main__":
    main()
