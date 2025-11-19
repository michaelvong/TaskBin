# routes/delete_board.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="DELETE /boards/{boardId}",
    lambda_name="TaskBin_DeleteBoard"
)
