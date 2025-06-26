# test_builder_flask_app_manager.py

import pytest
import json
from unittest.mock import patch, MagicMock
from bisslog_flask.builder.builder_flask_app_manager import BuilderFlaskAppManager
from bisslog_flask.builder.static_python_construct_data import StaticPythonConstructData
from bisslog_schema.schema import TriggerHttp, TriggerWebsocket
from bisslog_schema.use_case_code_inspector.use_case_code_metadata import (
    UseCaseCodeInfoClass, UseCaseCodeInfoObject, UseCaseCodeInfo
)


@pytest.mark.parametrize("n_params,expected", [
    (0, "setup_func()"),
    (1, "setup_func(\"flask\")"),
    (2, "setup_func(\"flask\")  # TODO: change this")
])
@patch("bisslog_flask.builder.builder_flask_app_manager.get_setup_metadata")
def test_get_bisslog_setup_with_setup_function(mock_get_setup, n_params, expected):
    setup_func = MagicMock(function_name="setup_func", module="setup_module", n_params=n_params)
    mock_get_setup.return_value = MagicMock(setup_function=setup_func, runtime={})
    result = BuilderFlaskAppManager(lambda x: None)._get_bisslog_setup("something")
    assert expected in result.build
    assert "setup_module" in result.importing


@patch("bisslog_flask.builder.builder_flask_app_manager.get_setup_metadata")
def test_get_bisslog_setup_with_runtime_fallback(mock_get_setup):
    runtime_func = MagicMock(function_name="custom_setup", module="runtime_module")
    mock_get_setup.return_value = MagicMock(setup_function=None, runtime={"flask": runtime_func})
    result = BuilderFlaskAppManager(lambda x: None)._get_bisslog_setup("something")
    assert "custom_setup()" in result.build
    assert "runtime_module" in result.importing


@patch("bisslog_flask.builder.builder_flask_app_manager.get_setup_metadata", return_value=None)
def test_get_bisslog_setup_none(mock_get_setup):
    result = BuilderFlaskAppManager(lambda x: None)._get_bisslog_setup("something")
    assert result is None


def test_generate_use_case_code_build_class():
    uc = UseCaseCodeInfoClass(name="my_uc", docs="", module="mymodule", class_name="MyClass")
    name, result = BuilderFlaskAppManager._generate_use_case_code_build(uc)
    assert name == "my_uc_uc"
    assert "MyClass()" in result.build


def test_generate_use_case_code_build_object():
    uc = UseCaseCodeInfoObject(name="my_uc", docs="", module="mymodule", var_name="uc_var")
    name, result = BuilderFlaskAppManager._generate_use_case_code_build(uc)
    assert name == "uc_var"
    assert result.build == ""


def test_generate_use_case_code_build_invalid_type():
    with pytest.raises(ValueError):
        class Invalid(UseCaseCodeInfo): pass
        BuilderFlaskAppManager._generate_use_case_code_build(Invalid("x", "", ""))


def test_generate_use_case_code_http_trigger_without_mapper():
    trigger = TriggerHttp(path="/hello", method="POST", mapper=None)
    uc_info = UseCaseCodeInfoClass(name="myuc", docs="", module="mymod", class_name="UCClass")
    result = BuilderFlaskAppManager._generate_use_case_code_http_trigger(
        "my_uc", "my_uc_uc", uc_info, trigger, 1)
    assert "def my_uc_handler_1()" in result.body
    assert "my_uc_uc(**kwargs)" in result.body
    assert "request.get_json" in result.body


def test_generate_use_case_code_http_trigger_with_mapper():
    trigger = TriggerHttp(path="/hi", method="GET", mapper={"body": {"x": "int"}})
    uc_info = UseCaseCodeInfoClass(name="myuc", docs="", module="mymod", class_name="UCClass")
    result = BuilderFlaskAppManager._generate_use_case_code_http_trigger(
        "my_uc", "my_uc_uc", uc_info, trigger, 2)
    assert "res_map" in result.body
    assert "my_uc_uc(**res_map)" in result.body


def test_generate_use_case_code_websocket_trigger_with_mapper():
    trigger = TriggerWebsocket(route_key="room", mapper={"body": {"msg": "str"}})
    uc_info = UseCaseCodeInfoObject(name="ws_uc", docs="", module="wsmod", var_name="ws_callable")
    result = BuilderFlaskAppManager._generate_use_case_code_websocket_trigger(
        "chat", "ws_callable", uc_info, trigger, 0)
    assert "res_map = chat_ws_mapper_0.map" in result.build
    assert "@sock.route(\"/ws/room\")" in result.build
    assert "ws.send(response)" in result.build


def test_generate_use_case_code_websocket_trigger_without_mapper():
    trigger = TriggerWebsocket(route_key=None, mapper=None)
    uc_info = UseCaseCodeInfoObject(name="ws_uc", docs="", module="wsmod", var_name="ws_callable")
    result = BuilderFlaskAppManager._generate_use_case_code_websocket_trigger(
        "chat", "ws_callable", uc_info, trigger, 1)
    assert "payload = json.loads(data)" in result.build
    assert "ws_callable(**payload)" in result.build
    assert "@sock.route(\"/ws/chat.default\")" in result.build
