import pytest
from flask import Flask
from unittest.mock import MagicMock

from bisslog_flask.initializer.init_flask_app_manager import InitFlaskAppManager
from bisslog_schema.schema import TriggerInfo
from bisslog_schema.schema.triggers.trigger_http import TriggerHttp
from bisslog_schema.schema.triggers.trigger_websocket import TriggerWebsocket
from bisslog_schema.schema.use_case_info import UseCaseInfo
from types import SimpleNamespace


@pytest.fixture
def fake_use_case_info():
    http_trigger = TriggerInfo(keyname="http_trigger", type="http", options=TriggerHttp(method="GET", path="/test"))
    ws_trigger = TriggerInfo(keyname="ws_trigger", type="websocket", options=TriggerWebsocket(route_key="message"))

    return UseCaseInfo(
        keyname="sample_uc",
        name="Sample Use Case",
        description="desc",
        type="sync",
        triggers=[http_trigger, ws_trigger]
    )


@pytest.fixture
def mock_read_service_info_with_code(fake_use_case_info):
    return SimpleNamespace(
        declared_metadata=SimpleNamespace(
            name="TestService",
            use_cases={"sample_uc": fake_use_case_info}
        ),
        discovered_use_cases={"sample_uc": lambda: {"ok": True}}
    )


def test_init_flask_app_registers_routes(monkeypatch, fake_use_case_info, mock_read_service_info_with_code):
    # Arrange
    mock_http = MagicMock()
    mock_ws = MagicMock()

    # Patch the metadata reader
    monkeypatch.setattr("bisslog_flask.initializer.init_flask_app_manager.read_service_info_with_code",
                        lambda *args, **kwargs: mock_read_service_info_with_code)

    app_manager = InitFlaskAppManager(http_processor=mock_http, websocket_processor=mock_ws)

    # Act
    app = app_manager(metadata_file="metadata.yml", use_cases_folder_path="src/uc")

    # Assert
    assert isinstance(app, Flask)
    mock_http.assert_called_once()
    mock_ws.assert_called_once()



def test_existing_app_is_used(monkeypatch, fake_use_case_info, mock_read_service_info_with_code):
    app = Flask("ExistingApp")

    monkeypatch.setattr("bisslog_flask.initializer.init_flask_app_manager.read_service_info_with_code",
                        lambda *args, **kwargs: mock_read_service_info_with_code)

    mock_http = MagicMock()
    mock_ws = MagicMock()

    app_manager = InitFlaskAppManager(http_processor=mock_http, websocket_processor=mock_ws)
    result = app_manager(metadata_file="x", use_cases_folder_path="x", app=app)

    assert result is app
