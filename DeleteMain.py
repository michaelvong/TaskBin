from TaskBin.DeleteScript.DeleteUserpool import delete_user_pool
from TaskBin.DeleteScript.DeleteDB import delete_table
import time

def main():
    delete_user_pool()
    success = delete_table()
    if success:
        print("DynamoDB table deletion complete.")
    else:
        print("DynamoDB table deletion failed.")

if __name__ == "__main__":
    main()