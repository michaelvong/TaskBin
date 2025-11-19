# routes/generate_code.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="POST /boards/{boardId}/code",
    lambda_name="TaskBin_GenerateCode"
)
