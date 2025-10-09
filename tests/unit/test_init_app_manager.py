from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from bisslog_schema.schema import TriggerInfo
from bisslog_schema.schema.triggers.trigger_http import TriggerHttp
from bisslog_schema.schema.triggers.trigger_websocket import TriggerWebsocket
from bisslog_schema.schema.use_case_info import UseCaseInfo
from flask import Flask

from bisslog_flask.initializer.init_flask_app_manager import InitFlaskAppManager


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
def fake_use_case_info_with_async():
    http_trigger = TriggerInfo(keyname="http_trigger", type="http", options=TriggerHttp(method="GET", path="/test2"))

    return UseCaseInfo(
        keyname="sample_coroutine_uc",
        name="sample_coroutine_uc",
        description="desc",
        type="async",
        triggers=[http_trigger]
    )

@pytest.fixture
def fake_force_import():
    force_import = MagicMock()
    return force_import


@pytest.fixture
def mock_read_service_info_with_code(fake_use_case_info, fake_use_case_info_with_async):

    async def mock_coroutine(*args, **kwargs):
        return {"sample_coroutine_res": 23}

    return SimpleNamespace(
        declared_metadata=SimpleNamespace(
            name="TestService",
            use_cases={"sample_uc": fake_use_case_info, "sample_coroutine_uc": fake_use_case_info_with_async}
        ),
        discovered_use_cases={"sample_uc": lambda: {"ok": True}, "sample_coroutine_uc": mock_coroutine},
    )


def test_init_flask_app_registers_routes(monkeypatch, fake_use_case_info,
                                         mock_read_service_info_with_code, fake_force_import):
    # Arrange
    mock_http = MagicMock()
    mock_ws = MagicMock()

    # Patch the metadata reader
    monkeypatch.setattr("bisslog_flask.initializer.init_flask_app_manager.read_service_info_with_code",
                        lambda *args, **kwargs: mock_read_service_info_with_code)

    app_manager = InitFlaskAppManager(http_processor=mock_http, websocket_processor=mock_ws, force_import=fake_force_import)

    # Act
    app = app_manager(metadata_file="metadata.yml", use_cases_folder_path="src/uc")

    # Assert
    assert isinstance(app, Flask)
    assert mock_http.call_count == 2
    mock_ws.assert_called_once()



def test_existing_app_is_used(monkeypatch, fake_use_case_info, mock_read_service_info_with_code, fake_force_import):
    app = Flask("ExistingApp")

    monkeypatch.setattr("bisslog_flask.initializer.init_flask_app_manager.read_service_info_with_code",
                        lambda *args, **kwargs: mock_read_service_info_with_code)

    mock_http = MagicMock()
    mock_ws = MagicMock()

    app_manager = InitFlaskAppManager(http_processor=mock_http, websocket_processor=mock_ws,
                                      force_import=fake_force_import)
    result = app_manager(metadata_file="x", use_cases_folder_path="x", app=app)

    assert result is app
