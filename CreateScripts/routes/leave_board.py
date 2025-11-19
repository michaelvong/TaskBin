# routes/leave_board.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="POST /boards/{boardId}/leave",
    lambda_name="TaskBin_LeaveBoard"
)