
from __future__ import annotations

from flask import Flask
from unittest.mock import Mock
import flask
import pytest

from bisslog_flask.initializer.bisslog_flask_http_resolver import BisslogFlaskHttpResolver

pytestmark = pytest.mark.skipif(
    tuple(map(int, flask.__version__.split(".")[:2])) < (2, 2),
    reason="Async views need Flask >= 2.2",
)

@pytest.fixture
def app():
    return Flask(__name__)


def test_lambda_fn_without_mapper_get_does_not_include_body(app):
    called = {}

    def uc(**kwargs):
        called.update(kwargs)
        return {"ok": True}

    with app.test_request_context("/items/42?q=abc", method="GET"):
        resp = BisslogFlaskHttpResolver._lambda_fn(fn=uc, __mapper__=None, id="42")
        assert resp.mimetype == "application/json"
        assert resp.get_json() == {"ok": True}

    assert called == {"id": "42"}


def test_lambda_fn_without_mapper_post_includes_body(app):
    captured = {}

    def uc(**kwargs):
        captured.update(kwargs)
        return {"received": kwargs}

    with app.test_request_context("/echo", method="POST", json={"a": 1, "b": "x"}):
        resp = BisslogFlaskHttpResolver._lambda_fn(fn=uc, __mapper__=None)
        assert resp.status_code == 200
        assert resp.get_json() == {"received": {"a": 1, "b": "x"}}

    assert captured == {"a": 1, "b": "x"}


def test_lambda_fn_with_mapper_maps_all_parts_and_calls_uc(app):
    class FakeMapper:
        def __init__(self):
            self.last_input = None
        def map(self, payload):
            self.last_input = payload
            return {"x": 99}

    mapper = FakeMapper()
    uc = Mock(return_value={"ok": True})

    with app.test_request_context(
        "/do/7?key=vv",
        method="POST",
        json={"foo": 1},
        headers={"X-Test": "hdr"},
    ):
        from flask import request
        request.view_args = {"id": "7"}

        resp = BisslogFlaskHttpResolver._lambda_fn(fn=uc, __mapper__=mapper)

        assert resp.status_code == 200
        assert resp.get_json() == {"ok": True}

    inp = mapper.last_input
    assert set(inp.keys()) == {"path_query", "body", "params", "headers"}
    assert inp["path_query"] == {"id": "7"}
    assert inp["body"] == {"foo": 1}
    assert inp["params"] == {"key": "vv"}
    assert inp["headers"].get("X-Test") == "hdr"

    uc.assert_called_once_with(x=99)


def test_lambda_fn_returns_json_response_type(app):
    def uc():
        return {"hello": "world"}

    with app.test_request_context("/hi", method="GET"):
        resp = BisslogFlaskHttpResolver._lambda_fn(fn=uc, __mapper__=None)
        assert resp.mimetype == "application/json"
        assert resp.get_json() == {"hello": "world"}
