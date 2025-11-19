# routes/list_user_tasks.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="GET /users/{user_id}/tasks",
    lambda_name="TaskBin_ListUserTasks"
)