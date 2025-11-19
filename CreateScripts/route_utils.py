import boto3
import json
import os
from pathlib import Path

current_dir = Path(__file__).parent
arns_path = current_dir / "lambda_arns.json"

class RouteIntegration:
    def __init__(self, api_id=None, region="us-west-1"):
        self.api_id = api_id or os.environ.get('API_ID')
        self.region = region
        self.client = boto3.client('apigatewayv2', region_name=region)
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.lambda_arns = self._load_lambda_arns()

        if not self.api_id:
            raise ValueError("API ID not provided and not found in environment")

    def _load_lambda_arns(self):
        """Load Lambda ARNs from lambda_arns.json"""
        try:
            with open(arns_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: lambda_arns.json not found")
            return {}

    def create_route(self, route_key, lambda_name, authorization_type="NONE"):
        """
        Create a complete route with Lambda integration

        Args:
            route_key: The route path and method (e.g., "POST /boards")
            lambda_name: Name of the Lambda function (must exist in lambda_arns.json)
            authorization_type: Authorization type (default: "NONE")
        """
        if lambda_name not in self.lambda_arns:
            raise ValueError(f"Lambda {lambda_name} not found in lambda_arns.json")

        lambda_arn = self.lambda_arns[lambda_name]

        try:
            # Step 1: Create Integration
            integration_response = self.client.create_integration(
                ApiId=self.api_id,
                IntegrationType='AWS_PROXY',
                IntegrationUri=lambda_arn,
                PayloadFormatVersion='2.0'
            )
            integration_id = integration_response['IntegrationId']
            print(f"  Created integration: {integration_id}")

            # Step 2: Create Route
            route_response = self.client.create_route(
                ApiId=self.api_id,
                RouteKey=route_key,
                Target=f'integrations/{integration_id}',
                AuthorizationType=authorization_type
            )
            print(f"  Created route: {route_key}")

            # Step 3: Grant API Gateway permission to invoke Lambda
            self._add_lambda_permission(lambda_arn, route_key)

            return {
                'route_id': route_response['RouteId'],
                'integration_id': integration_id
            }

        except Exception as e:
            print(f"  Error creating route {route_key}: {str(e)}")
            raise

    def _add_lambda_permission(self, lambda_arn, route_key):
        """Add permission for API Gateway to invoke Lambda"""
        try:
            # Extract function name and account ID from ARN
            function_name = lambda_arn.split(':')[-1]
            account_id = lambda_arn.split(':')[4]

            # Create a valid statement ID (alphanumeric, hyphens, underscores only)
            # Remove special characters like {}, /, spaces
            statement_id = f"apigateway-{self.api_id}-{route_key}"
            statement_id = statement_id.replace(' ', '-').replace('/', '-').replace('{', '').replace('}', '')

            self.lambda_client.add_permission(
                FunctionName=function_name,
                StatementId=statement_id,
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f'arn:aws:execute-api:{self.region}:{account_id}:{self.api_id}/*'
            )
            print(f"  Granted Lambda permission")
        except self.lambda_client.exceptions.ResourceConflictException:
            print(f"  Permission already exists")
        except Exception as e:
            print(f"  Warning: Could not add Lambda permission: {str(e)}")

    def delete_route(self, route_id):
        """Delete a route"""
        try:
            self.client.delete_route(
                ApiId=self.api_id,
                RouteId=route_id
            )
            print(f"Deleted route: {route_id}")
        except Exception as e:
            print(f"Error deleting route: {str(e)}")