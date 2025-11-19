# routes/edit_board.py
from TaskBin.CreateScripts.route_utils import RouteIntegration

integration = RouteIntegration()
integration.create_route(
    route_key="PATCH /boards/{board_id}",
    lambda_name="TaskBin_EditBoard"
)