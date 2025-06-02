import pytest
from flask import Flask
from flask_socketio import SocketIO
from unittest.mock import Mock, MagicMock

from bisslog_flask.initializer.bisslog_flask_ws_resolver import BisslogFlaskWebSocketResolver
from bisslog_schema.schema import UseCaseInfo, TriggerInfo, TriggerConsumer
from bisslog_schema.schema.triggers.trigger_websocket import TriggerWebsocket


@pytest.fixture
def use_case_info():
    return UseCaseInfo(
        keyname="ws_test",
        name="WS Test",
        description="WebSocket use case",
        type="sync",
        triggers=[]
    )


@pytest.fixture
def trigger_websocket():
    return TriggerInfo(
        keyname="ws_trigger",
        type="websocket",
        options=TriggerWebsocket(route_key="message", mapper=None)
    )


def test_event_handler_invokes_callable(use_case_info, trigger_websocket):
    app = Flask(__name__)
    socketio = SocketIO(app, cors_allowed_origins="*")
    app.extensions["socketio"] = socketio

    mock_callable = Mock(return_value={"response": "ok"})

    resolver = BisslogFlaskWebSocketResolver()
    resolver(app, use_case_info, trigger_websocket, mock_callable)

    client = socketio.test_client(app)

    # Emit WebSocket event
    client.emit("message", {"hello": "world"})

    # Validate it was invoked
    mock_callable.assert_called_once_with({"hello": "world"})

    client.disconnect()

def test_event_handler_invokes_callable_instantiating_in_runtime(use_case_info, trigger_websocket):
    app = Flask(__name__)

    mock_callable = Mock(return_value={"response": "ok"})

    resolver = BisslogFlaskWebSocketResolver()
    resolver(app, use_case_info, trigger_websocket, mock_callable)

    socketio = app.extensions["socketio"]
    client = socketio.test_client(app)

    # Emit WebSocket event
    client.emit("message", {"hello": "world"})

    # Validate it was invoked
    mock_callable.assert_called_once_with({"hello": "world"})

    client.disconnect()


def test_event_handler_not_doing_anything(use_case_info):
    app = Flask(__name__)
    mock_callable = Mock(return_value={"response": "ok"})
    trigger_info = TriggerInfo(type="consumer", keyname="do_something",
                               options=MagicMock(spec=TriggerConsumer))
    resolver = BisslogFlaskWebSocketResolver()
    resolver(app, use_case_info, trigger_info, mock_callable)
