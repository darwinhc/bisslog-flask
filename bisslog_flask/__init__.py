"""
bisslog_flask

An extension of the `bisslog` library to support service orchestration via Flask.

This package enables dynamic registration of HTTP and WebSocket routes in a Flask
application, using declarative metadata (YAML/JSON). It promotes clean separation
between application logic and infrastructure concerns, aligning with hexagonal
or clean architecture principles.


Requirements
------------
- Flask >= 2.0
- bisslog-schema >= 0.0.3
- flask-cors
- (optional) flask-socketio for WebSocket integration

License
-------
MIT © Darwin Stiven Herrera Cartagena
"""
from .initializer.init_flask_app_manager import BisslogFlask
from .socket_helper.socket_helper import BisslogFlaskSocketHelper

__all__ = ["BisslogFlask", "BisslogFlaskSocketHelper"]
