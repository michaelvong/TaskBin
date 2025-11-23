# routes/get_board.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()

# Single board GET
integration.create_route(
    route_key="GET /boards/{board_id}",
    lambda_name="TaskBin_GetBoard"
)

# Batch boards GET via query parameters
integration.create_route(
    route_key="GET /boards",
    lambda_name="TaskBin_GetBoard"
)
