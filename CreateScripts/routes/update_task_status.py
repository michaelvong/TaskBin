# routes/update_task_status.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="PATCH /boards/{board_id}/tasks/{task_id}",
    lambda_name="TaskBin_UpdateTaskStatus"
)