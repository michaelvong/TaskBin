# routes/join_board.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="POST /boards/{boardId}/join",
    lambda_name="TaskBin_JoinBoard"
)