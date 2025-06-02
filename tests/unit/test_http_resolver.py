import pytest
from flask import Flask
from unittest.mock import Mock

from bisslog_flask.initializer.bisslog_flask_http_resolver import BisslogFlaskHttpResolver
from bisslog_schema.schema import UseCaseInfo, TriggerHttp, TriggerInfo


@pytest.fixture
def flask_app():
    app = Flask(__name__)
    return app


@pytest.fixture
def resolver():
    return BisslogFlaskHttpResolver()


def test_register_get_route_without_mapper(flask_app, resolver):
    def mock_uc():
        return {"status": "ok"}

    use_case_info = UseCaseInfo(
        keyname="test_uc", name="Test UC", description="", type="sync", triggers=[]
    )
    trigger_http = TriggerHttp(method="GET", path="/test", allow_cors=False)
    trigger = TriggerInfo(keyname="test_trigger", type="http", options=trigger_http)

    resolver(flask_app, use_case_info, trigger, mock_uc)

    client = flask_app.test_client()
    response = client.get("/test")

    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_register_post_route_with_json(flask_app, resolver):
    def mock_uc(**data):
        return {"echo": data.get("name")}

    use_case_info = UseCaseInfo(
        keyname="echo_uc", name="Echo UC", description="", type="sync", triggers=[]
    )
    trigger_http = TriggerHttp(method="POST", path="/echo", allow_cors=False)
    trigger = TriggerInfo(keyname="echo_trigger", type="http", options=trigger_http)

    resolver(flask_app, use_case_info, trigger, mock_uc)

    client = flask_app.test_client()
    response = client.post("/echo", json={"name": "ChatGPT"})

    assert response.status_code == 200
    assert response.json == {"echo": "ChatGPT"}


def test_register_post_route_with_mapper(flask_app, resolver):
    def mock_uc(*, a = None, b = None, c = None, d = None, e = None, f = None):
        return {"a": a, "b": b, "c": c, "d": d, "e": e, "f": f}

    use_case_info = UseCaseInfo(
        keyname="echo_uc", name="Echo UC", description="", type="sync", triggers=[]
    )
    trigger_http = TriggerHttp(method="POST", path="/echo/{algo3}", allow_cors=False,
                               mapper={"body.algo1": "a", "body.algo2": "b",
                                       "path_query.algo3": "c", "headers.algo4": "d",
                                       "params.algo5": "e", "params.algo6": "f"})
    trigger = TriggerInfo(keyname="echo_trigger", type="http", options=trigger_http)

    resolver(flask_app, use_case_info, trigger, mock_uc)

    client = flask_app.test_client()
    response = client.post("/echo/something", json={"algo1": 2356, "algo2": "casa"},
                           headers=[("algo4", "prueba4")], query_string={"algo5": 7554, "algo6": "prueba6"})

    assert response.status_code == 200
    assert response.json["a"] == 2356
    assert response.json["b"] == "casa"
    assert response.json["c"] == "something"
    assert response.json["d"] == "prueba4"
    assert response.json["e"] == "7554"
    assert response.json["f"] == "prueba6"

def test_invalid_trigger_type_is_ignored(flask_app, resolver):
    trigger = TriggerInfo(keyname="invalid", type="websocket", options=Mock())
    mock_uc = Mock()
    use_case_info = UseCaseInfo(
        keyname="invalid_uc", name="", description="", type="sync", triggers=[]
    )

    resolver(flask_app, use_case_info, trigger, mock_uc)

    client = flask_app.test_client()
    response = client.get("/invalid")

    assert response.status_code == 404
