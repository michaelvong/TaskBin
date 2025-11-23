# routes/get_task.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()

# Single task GET
integration.create_route(
    route_key="GET /tasks/{task_id}",
    lambda_name="TaskBin_GetTask"
)

# Batch tasks GET via query parameters
integration.create_route(
    route_key="GET /tasks",
    lambda_name="TaskBin_GetTask"
)
