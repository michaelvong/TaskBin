# routes/edit_task.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="PATCH /boards/tasks/{task_id}",
    lambda_name="TaskBin_EditTask"
)