"""
WebSocket resolver for Bisslog-based Flask applications using Flask-SocketIO.

This module defines the `BisslogFlaskWebSocketResolver` class, which dynamically registers
WebSocket-based use case triggers in a Flask app. The class uses metadata definitions to
configure event routes (via `route_key`) and binds them to corresponding use case functions.
"""
from typing import Callable
from flask import Flask, request

try:
    from flask_socketio import SocketIO
except ImportError:
    class SocketIO:
        """Socket IO simulator while is not installed"""
        def __init__(self, _, ** __):
            raise ImportError("flask socketio is not installed, please install it")

from bisslog.utils.mapping import Mapper
from bisslog_schema.schema import UseCaseInfo, TriggerInfo
from bisslog_schema.schema.triggers.trigger_websocket import TriggerWebsocket
from .bisslog_flask_resolver import BisslogFlaskResolver


class BisslogFlaskWebSocketResolver(BisslogFlaskResolver):
    """
    Resolver that registers WebSocket use cases using Flask-SocketIO.

    This class maps WebSocket events (via route_key) to the use case callables.
    If a SocketIO instance is not already attached to the Flask app,
    a new one will be created and stored in `app.extensions["socketio"]`.
    """

    def __call__(self, app: Flask, use_case_info: UseCaseInfo,
                 trigger_info: TriggerInfo, use_case_callable: Callable, **kwargs):
        """
        Register a WebSocket event handler for a use case.

        Parameters
        ----------
        app : Flask
            The Flask app instance.
        use_case_info : UseCaseInfo
            Metadata about the use case.
        trigger_info : TriggerWebsocket
            Trigger options containing the route_key and mapper.
        use_case_callable : Callable
            The actual use case function to call when the event is triggered.
        kwargs : dict
            Additional optional arguments (ignored here).
        """
        if not isinstance(trigger_info.options, TriggerWebsocket):
            return

        # Get or create SocketIO instance
        socket_io_obj = app.extensions.get("socketio")
        if socket_io_obj is None:
            socket_io_obj = SocketIO(app, cors_allowed_origins="*")
            app.extensions["socketio"] = socket_io_obj

        route_key = trigger_info.options.route_key
        mapper = Mapper(
            name=f"mapper-ws-{use_case_info.keyname}-{route_key}",
            base=trigger_info.options.mapper
        ) if trigger_info.options.mapper else None

        @socket_io_obj.on(route_key)
        def on_event(data):
            mapped_data = mapper.map({
                "route_key": route_key,
                "connection_id": request.sid,
                "body": data,
                "headers": dict(request.headers)
            }) if mapper else data

            return use_case_callable(**mapped_data) if mapper else use_case_callable(data)
