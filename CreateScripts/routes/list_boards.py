# routes/list_boards.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="GET /users/{user_id}/boards",
    lambda_name="TaskBin_ListBoards"
)