# routes/list_board_members.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="GET /boards/{board_id}/members",
    lambda_name="TaskBin_ListBoardMembers"
)