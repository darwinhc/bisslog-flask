"""
Flask application initializer for Bisslog-based services.

This module defines a manager that reads service metadata and dynamically registers
use case endpoints into a Flask application using resolvers for HTTP and WebSocket triggers.

Classes
-------
InitFlaskAppManager : Initializes a Flask app with routes from use case metadata.

Dependencies
------------
- Flask
- bisslog_schema
- BisslogFlaskResolver
"""

from typing import Optional, Callable

from bisslog_schema import read_service_info_with_code
from bisslog_schema.schema import UseCaseInfo, TriggerHttp, TriggerWebsocket
from flask import Flask

from .bisslog_flask_http_resolver import BisslogFlaskHttpResolver
from .bisslog_flask_resolver import BisslogFlaskResolver
from .bisslog_flask_ws_resolver import BisslogFlaskWebSocketResolver


class InitFlaskAppManager:
    """
    Initializes a Flask app by registering routes from metadata using HTTP and WebSocket resolvers.

    This manager reads metadata and code, then applies the appropriate processor (resolver)
    to each use case according to its trigger type.

    Parameters
    ----------
    http_processor : BisslogFlaskResolver
        Resolver used to handle HTTP-triggered use cases.
    websocket_processor : BisslogFlaskResolver
        Resolver used to handle WebSocket-triggered use cases.
    """

    def __init__(self, http_processor: BisslogFlaskResolver,
                 websocket_processor: BisslogFlaskResolver) -> None:
        self._http_processor = http_processor
        self._websocket_processor = websocket_processor

    def __call__(
            self,
            metadata_file: Optional[str] = None,
            use_cases_folder_path: Optional[str] = None,
            app: Optional[Flask] = None,
            *,
            encoding: str = "utf-8",
            secret_key: Optional[str] = None,
            jwt_secret_key: Optional[str] = None,
            **kwargs) -> Flask:
        """
        Loads metadata, discovers use case functions, registers routes and returns the Flask app.

        This method reads metadata and code from the given paths, initializes the Flask app
        (if not provided), configures security options, and applies HTTP or WebSocket processors
        based on the trigger type for each use case.

        Parameters
        ----------
        metadata_file : str, optional
            Path to the metadata file (YAML/JSON).
        use_cases_folder_path : str, optional
            Directory where use case code is located.
        app : Flask, optional
            An existing Flask app instance to which routes will be added.
            If not provided, a new app is created using the service name.
        encoding : str, optional
            File encoding for reading metadata (default is "utf-8").
        secret_key : str, optional
            Secret key to set in app config (used for session security).
        jwt_secret_key : str, optional
            JWT secret key to set in app config (used for token authentication).
        **kwargs : Any
            Additional keyword arguments (not currently used).

        Returns
        -------
        Flask
            The Flask app instance with registered use case routes.
        """
        full_service_data = read_service_info_with_code(
            metadata_file=metadata_file,
            use_cases_folder_path=use_cases_folder_path,
            encoding=encoding
        )
        service_info = full_service_data.declared_metadata
        use_cases = full_service_data.discovered_use_cases

        # Initialize Flask app
        if app is None:
            app = Flask(service_info.name)

        # Configure security
        if secret_key is not None:
            app.config["SECRET_KEY"] = secret_key
        if jwt_secret_key is not None:
            app.config["JWT_SECRET_KEY"] = jwt_secret_key

        # Register each use case to the appropriate processor
        for use_case_keyname in service_info.use_cases:
            use_case_info: UseCaseInfo = service_info.use_cases[use_case_keyname]
            use_case_callable: Callable = use_cases[use_case_keyname]

            for trigger in use_case_info.triggers:
                if isinstance(trigger.options, TriggerHttp):
                    self._http_processor(
                        app, use_case_info, trigger, use_case_callable, **kwargs)
                if isinstance(trigger.options, TriggerWebsocket):
                    self._websocket_processor(
                        app, use_case_info, trigger, use_case_callable, **kwargs)

        return app


BisslogFlask = InitFlaskAppManager(BisslogFlaskHttpResolver(), BisslogFlaskWebSocketResolver())
