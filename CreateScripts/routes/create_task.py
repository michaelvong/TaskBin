# routes/create_task.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="POST /boards/{board_id}/tasks/create",
    lambda_name="TaskBin_CreateTask"
)