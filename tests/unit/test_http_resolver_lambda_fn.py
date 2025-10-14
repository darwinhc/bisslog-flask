# test_bisslog_flask_http_resolver_lambda_fn.py
from __future__ import annotations

from flask import Flask
from unittest.mock import Mock

import pytest

from bisslog_flask.initializer.bisslog_flask_http_resolver import BisslogFlaskHttpResolver


@pytest.fixture
def app():
    return Flask(__name__)


def test_lambda_fn_without_mapper_get_does_not_include_body(app):
    called = {}

    def uc(**kwargs):
        called.update(kwargs)
        return {"ok": True}

    # GET con query y path param; body no se debe pasar
    with app.test_request_context("/items/42?q=abc", method="GET"):
        # Simulamos path params vía kwargs (Flask los pondría como view_args al despachar)
        resp = BisslogFlaskHttpResolver._lambda_fn(fn=uc, __mapper__=None, id="42")
        assert resp.mimetype == "application/json"
        assert resp.get_json() == {"ok": True}

    assert called == {"id": "42"}  # nada de body ni params


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
    # Fake mapper que solo devuelve {'x': 99} y nos deja inspeccionar el input
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
        # Simulamos path param 'id' via request.view_args:
        # Como invocamos estático, no hay enrutamiento de Flask; pasamos el kw para que _lambda_fn
        # lo incluya en path_query a través de request.view_args (lo emula Flask internamente),
        # así que lo agregamos manualmente:
        # Nota: cuando se usa test_request_context, podemos anexar view_args así:
        from flask import request
        request.view_args = {"id": "7"}

        resp = BisslogFlaskHttpResolver._lambda_fn(fn=uc, __mapper__=mapper)

        assert resp.status_code == 200
        assert resp.get_json() == {"ok": True}

    # Verifica que el mapper recibió las 4 secciones
    inp = mapper.last_input
    assert set(inp.keys()) == {"path_query", "body", "params", "headers"}
    assert inp["path_query"] == {"id": "7"}
    assert inp["body"] == {"foo": 1}
    assert inp["params"] == {"key": "vv"}
    # headers es un EnvironHeaders; verificamos que esté el nuestro
    assert inp["headers"].get("X-Test") == "hdr"

    # Verifica que el UC fue llamado con el resultado del mapper
    uc.assert_called_once_with(x=99)


def test_lambda_fn_returns_json_response_type(app):
    def uc():
        return {"hello": "world"}

    with app.test_request_context("/hi", method="GET"):
        resp = BisslogFlaskHttpResolver._lambda_fn(fn=uc, __mapper__=None)
        assert resp.mimetype == "application/json"
        assert resp.get_json() == {"hello": "world"}
