# test_builder_flask_app_manager_call.py

import pytest
from unittest.mock import patch, MagicMock
from bisslog_flask.builder.builder_flask_app_manager import BuilderFlaskAppManager
from bisslog_flask.builder.static_python_construct_data import StaticPythonConstructData
from bisslog_schema.schema import TriggerHttp, TriggerWebsocket, UseCaseInfo
from bisslog_schema.use_case_code_inspector.use_case_code_metadata import (
    UseCaseCodeInfoClass, UseCaseCodeInfoObject
)


@patch("bisslog_flask.builder.builder_flask_app_manager.read_full_service_metadata")
@patch.object(BuilderFlaskAppManager, "_get_bisslog_setup")
@patch.object(BuilderFlaskAppManager, "_generate_security_code")
@patch.object(BuilderFlaskAppManager, "_generate_use_case_code_build")
@patch.object(BuilderFlaskAppManager, "_generate_use_case_code_http_trigger")
@patch.object(BuilderFlaskAppManager, "_generate_use_case_code_websocket_trigger")
def test_call_generates_complete_flask_code(
    mock_ws_trigger,
    mock_http_trigger,
    mock_uc_build,
    mock_security,
    mock_setup,
    mock_read_metadata
):
    # Mock de respuesta del builder
    mock_setup.return_value = StaticPythonConstructData(build="# setup")
    mock_security.return_value = StaticPythonConstructData(build="# security")
    mock_uc_build.return_value = ("uc_instance", StaticPythonConstructData(build="# build"))
    mock_http_trigger.return_value = StaticPythonConstructData(build="# http")
    mock_ws_trigger.return_value = StaticPythonConstructData(build="# ws")

    # Mock metadata
    trigger_http = MagicMock(options=TriggerHttp(path="/hello", method="POST"))
    trigger_ws = MagicMock(options=TriggerWebsocket(route_key="msg"))
    use_case_info = UseCaseInfo(triggers=[trigger_http, trigger_ws])

    declared_metadata = MagicMock()
    declared_metadata.use_cases = {"my_use_case": use_case_info}

    discovered_use_cases = {
        "my_use_case": UseCaseCodeInfoClass(
            name="my_use_case", docs=None, module="uc_module", class_name="UseCase"
        )
    }

    mock_read_metadata.return_value = MagicMock(
        declared_metadata=declared_metadata,
        discovered_use_cases=discovered_use_cases
    )

    manager = BuilderFlaskAppManager()
    result = manager(metadata_file="file.yaml", use_cases_folder_path="./src")

    assert "Flask(__name__)" in result
    assert "# setup" in result
    assert "# security" in result
    assert "# build" in result
    assert "# http" in result
    assert "# ws" in result
    assert "app.run" in result
