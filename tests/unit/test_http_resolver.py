"""Tests for bisslog_flask.initializer.bisslog_flask_http_resolver."""

from __future__ import annotations

import asyncio
from unittest.mock import Mock

import pytest
import flask
from flask import Flask

from bisslog_schema.schema import UseCaseInfo, TriggerHttp, TriggerInfo
from bisslog_schema.schema.triggers.trigger_mappable import TriggerMappable

from bisslog_flask.initializer.bisslog_flask_http_resolver import BisslogFlaskHttpResolver


pytestmark = pytest.mark.skipif(
    tuple(map(int, flask.__version__.split(".")[:2])) < (2, 2),
    reason="Async views need Flask >= 2.2",
)

@pytest.fixture
def flask_app():
    app = Flask(__name__)
    return app


@pytest.fixture
def resolver():
    return BisslogFlaskHttpResolver()


def make_uc_info(key="uc"):
    return UseCaseInfo(
        keyname=key, name=key, description="", type="sync", triggers=[]
    )



def test_register_get_route_without_mapper(flask_app, resolver):
    def mock_uc():
        return {"status": "ok"}

    info = make_uc_info("test_uc")
    trig_http = TriggerHttp(method="GET", path="/test", allow_cors=False)
    trig = TriggerInfo(keyname="t", type="http", options=trig_http)

    resolver(flask_app, info, trig, mock_uc)

    client = flask_app.test_client()
    r = client.get("/test")

    assert r.status_code == 200
    assert r.json == {"status": "ok"}


def test_register_post_route_with_json(flask_app, resolver):
    def mock_uc(**data):
        return {"echo": data.get("name")}

    info = make_uc_info("echo_uc")
    trig_http = TriggerHttp(method="POST", path="/echo", allow_cors=False)
    trig = TriggerInfo(keyname="t", type="http", options=trig_http)

    resolver(flask_app, info, trig, mock_uc)

    client = flask_app.test_client()
    r = client.post("/echo", json={"name": "ChatGPT"})

    assert r.status_code == 200
    assert r.json == {"echo": "ChatGPT"}


def test_register_post_route_without_body_ok(flask_app, resolver):

    def mock_uc(**kwargs):
        return {"kwargs": kwargs}

    info = make_uc_info("no_body")
    trig_http = TriggerHttp(method="POST", path="/no-body", allow_cors=False)
    trig = TriggerInfo(keyname="t", type="http", options=trig_http)

    resolver(flask_app, info, trig, mock_uc)

    client = flask_app.test_client()
    r = client.post("/no-body")

    assert r.status_code == 200
    assert r.json == {"kwargs": {}}



def test_register_post_route_with_mapper(flask_app, resolver):
    def mock_uc(*, a=None, b=None, c=None, d=None, e=None, f=None):
        return {"a": a, "b": b, "c": c, "d": d, "e": e, "f": f}

    info = make_uc_info("echo_uc")
    mapper = {
        "body.algo1": "a",
        "body.algo2": "b",
        "path_query.algo3": "c",
        "headers.algo4": "d",
        "params.algo5": "e",
        "params.algo6": "f",
    }
    trig_http = TriggerHttp(
        method="POST",
        path="/echo/{algo3}",
        allow_cors=False,
        mapper=mapper,
    )
    assert isinstance(trig_http, TriggerMappable)
    trig = TriggerInfo(keyname="t", type="http", options=trig_http)

    resolver(flask_app, info, trig, mock_uc)

    client = flask_app.test_client()
    r = client.post(
        "/echo/something",
        json={"algo1": 2356, "algo2": "casa"},
        headers=[("algo4", "prueba4")],
        query_string={"algo5": 7554, "algo6": "prueba6"},
    )

    assert r.status_code == 200
    payload = r.get_json()
    assert payload["a"] == 2356
    assert payload["b"] == "casa"
    assert payload["c"] == "something"
    assert payload["d"] == "prueba4"
    assert payload["e"] == "7554"
    assert payload["f"] == "prueba6"



def test_register_async_function(flask_app, resolver):
    async def mock_uc(**data):
        await asyncio.sleep(0)
        return {"ok": True, "data": data}

    info = make_uc_info("async_fn")
    trig_http = TriggerHttp(method="POST", path="/async-fn", allow_cors=False)
    trig = TriggerInfo(keyname="t", type="http", options=trig_http)

    resolver(flask_app, info, trig, mock_uc)

    client = flask_app.test_client()
    r = client.post("/async-fn", json={"a": 1})
    assert r.status_code == 200
    assert r.json == {"ok": True, "data": {"a": 1}}


def test_register_async_callable_object(flask_app, resolver):
    class UC:
        async def __call__(self, *, a=None):
            await asyncio.sleep(0)
            return {"a": a}

    info = make_uc_info("async_obj")
    trig_http = TriggerHttp(
        method="POST",
        path="/async-obj",
        allow_cors=False,
        mapper={"body.a": "a"},
    )
    trig = TriggerInfo(keyname="t", type="http", options=trig_http)

    resolver(flask_app, info, trig, UC())

    client = flask_app.test_client()
    r = client.post("/async-obj", json={"a": 7})
    assert r.status_code == 200
    assert r.json == {"a": 7}



def test_invalid_trigger_type_is_ignored(flask_app, resolver):
    trig = TriggerInfo(keyname="invalid", type="websocket", options=Mock())
    mock_uc = Mock()
    info = make_uc_info("invalid_uc")

    resolver(flask_app, info, trig, mock_uc)

    client = flask_app.test_client()
    r = client.get("/invalid")
    assert r.status_code == 404


def test_endpoint_name_contains_key_and_path(flask_app, resolver):
    def mock_uc(id):
        return {"ok": 1}

    info = make_uc_info("keyX")
    trig_http = TriggerHttp(method="GET", path="/items/{id}", allow_cors=False)
    trig = TriggerInfo(keyname="t", type="http", options=trig_http)

    resolver(flask_app, info, trig, mock_uc)


    expected_rule = "keyX " + "/items/<id>"
    found = any(r.rule == "/items/<id>" and r.endpoint == expected_rule for r in flask_app.url_map.iter_rules())
    assert found

    client = flask_app.test_client()
    r = client.get("/items/42")
    assert r.status_code == 200
    assert r.json == {"ok": 1}



def test_cors_applied_when_allowed(monkeypatch, flask_app, resolver):

    captured = {}

    def fake_cross_origin(**kwargs):
        captured.update(kwargs)
        def decorator(fn):
            return fn
        return decorator


    import bisslog_flask.initializer.bisslog_flask_http_resolver as mod
    monkeypatch.setattr(mod, "cross_origin", fake_cross_origin, raising=True)

    def mock_uc():
        return {"ok": True}

    info = make_uc_info("cors_uc")
    trig_http = TriggerHttp(
        method="GET",
        path="/cors",
        allow_cors=True,
        allowed_origins=["https://a.com", "https://b.com"],
    )
    trig = TriggerInfo(keyname="t", type="http", options=trig_http)

    resolver(flask_app, info, trig, mock_uc)


    assert captured["origins"] == ["https://a.com", "https://b.com"]
    assert captured["methods"] == ["GET"]
    assert captured["supports_credentials"] is True
    assert "allow_headers" in captured

    client = flask_app.test_client()
    r = client.get("/cors")
    assert r.status_code == 200
    assert r.json == {"ok": True}


def test_cors_raises_when_flask_cors_missing(monkeypatch, flask_app):

    import bisslog_flask.initializer.bisslog_flask_http_resolver as mod
    monkeypatch.setattr(mod, "cross_origin", None, raising=True)

    resolver = BisslogFlaskHttpResolver()

    def mock_uc():
        return {"ok": True}

    info = make_uc_info("cors_missing")
    trig_http = TriggerHttp(method="GET", path="/cors-missing", allow_cors=True)
    trig = TriggerInfo(keyname="t", type="http", options=trig_http)

    with pytest.raises(ImportError):

        resolver(flask_app, info, trig, mock_uc)
