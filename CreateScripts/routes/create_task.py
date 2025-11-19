# routes/create_task.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="POST /boards/task/create",
    lambda_name="TaskBin_CreateTask"
)