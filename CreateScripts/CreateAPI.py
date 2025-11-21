import boto3
import json
import os
from pathlib import Path

# Directory of this script: TaskBin/CreateScripts/
SCRIPT_DIR = Path(__file__).resolve().parent

# Parent folder: TaskBin/
TASKBIN_DIR = SCRIPT_DIR.parent

# Routes directory inside TaskBin/CreateScripts/routes
ROUTES_DIRECT = os.path.join(os.path.dirname(__file__), "routes")


class APIOrchestrator:
    def __init__(self, api_name="TaskBin_API", region="us-west-1"):
        self.api_name = api_name
        self.region = region
        self.client = boto3.client('apigatewayv2', region_name=region)
        self.api_id = None

        # Save api_id.json inside TaskBin/
        self.api_id_file = TASKBIN_DIR / "api_id.json"

    def get_or_create_api(self):
        """Get existing API ID or create a new API"""

        # Check if API ID exists in file
        if self.api_id_file.exists():
            with open(self.api_id_file, 'r') as f:
                data = json.load(f)
                self.api_id = data.get('api_id')

            # Verify the API still exists
            try:
                self.client.get_api(ApiId=self.api_id)
                print(f"Using existing API: {self.api_id}")
                return self.api_id
            except self.client.exceptions.NotFoundException:
                print(f"API {self.api_id} not found, creating new one...")

        # Create new API
        response = self.client.create_api(
            Name=self.api_name,
            ProtocolType='HTTP',
            CorsConfiguration={
                'AllowOrigins': ['*'],
                'AllowMethods': ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
                'AllowHeaders': ['*']
            }
        )

        self.api_id = response['ApiId']

        # Save API ID to TaskBin/api_id.json
        with open(self.api_id_file, 'w') as f:
            json.dump({'api_id': self.api_id}, f, indent=2)

        print(f"Created new API: {self.api_id}")
        return self.api_id

    def create_all_routes(self):
        """Create all routes by running scripts in the routes folder"""
        routes_dir = Path(ROUTES_DIRECT)

        if not routes_dir.exists():
            print(f"Routes directory not found: {routes_dir}")
            return

        # Get all Python files in routes directory
        route_files = sorted(routes_dir.glob("*.py"))

        if not route_files:
            print("No route files found in routes directory")
            return

        print(f"\nCreating {len(route_files)} routes...")

        # Set environment variable for route scripts to use
        os.environ['API_ID'] = self.api_id

        for route_file in route_files:
            print(f"\nProcessing: {route_file.name}")
            try:
                # Execute the route script
                with open(route_file, 'r') as f:
                    exec(f.read(), {'__name__': '__main__'})
                print(f"✓ Successfully created route from {route_file.name}")
            except Exception as e:
                print(f"✗ Error processing {route_file.name}: {str(e)}")

    def deploy_api(self, stage_name="prod"):
        """Deploy the API to a stage"""
        try:
            response = self.client.create_stage(
                ApiId=self.api_id,
                StageName=stage_name,
                AutoDeploy=True
            )
            print(f"\n✓ API deployed to stage: {stage_name}")
            print(f"API Endpoint: https://{self.api_id}.execute-api.{self.region}.amazonaws.com/{stage_name}")
            return response
        except self.client.exceptions.ConflictException:
            print(f"Stage {stage_name} already exists")
        except Exception as e:
            print(f"Error deploying API: {str(e)}")


if __name__ == "__main__":
    orchestrator = APIOrchestrator()

    # Step 1: Get or create API
    api_id = orchestrator.get_or_create_api()

    # Step 2: Create all routes
    orchestrator.create_all_routes()

    # Step 3: Deploy API
    orchestrator.deploy_api()
