# routes/list_board_Tasks.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="GET /boards/{board_id}/tasks",
    lambda_name="TaskBin_ListBoardTasks"
)