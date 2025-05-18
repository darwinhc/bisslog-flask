"""
Flask Application Initializer for bisslog_schema with per-endpoint CORS

This module provides functionality to automatically create Flask routes
based on service metadata defined using bisslog_schema, with granular CORS control.
"""

import re
import importlib
import sys
from copy import deepcopy
from typing import Optional, Dict

from bisslog.utils.mapping import Mapper
from bisslog_schema.enums.trigger_type import TriggerEnum
from bisslog_schema.triggers.trigger_http import TriggerHttp
from bisslog_schema.triggers.trigger_info import TriggerInfo
from bisslog_schema.use_case_info import UseCaseInfo
from flask import Flask, request, jsonify
from flask_cors import CORS
from bisslog_schema import read_service_metadata


def _lambda_fn(*args, fn, __mapper__: Optional[Mapper], **kwargs):
    """Wrapper function to handle request data for use cases."""
    if __mapper__ is None:
        more_kwargs = {}
        if request.method.lower() not in ["get"]:
            more_kwargs.update(request.get_json(silent=True) or {})
        return fn(*args, **kwargs, **more_kwargs)

    res_map = __mapper__.map({
        "path_query": request.view_args or {},
        "body": request.get_json(silent=True) or {},
        "params": request.args.to_dict(),
        "headers": dict(request.headers),
    })
    res = fn(**res_map)

    return jsonify(res)


def _use_case_factory(use_case_name: str, fn: callable, mapper: Dict[str, str] = None):
    """Factory function to create use case view functions with optional mapping."""
    use_case_fn_copy = deepcopy(fn)
    if mapper is not None:
        mapper = Mapper(name=f"Mapper {use_case_name}", base=mapper)

    def uc(*args, **kwargs):
        return _lambda_fn(*args, fn=use_case_fn_copy, __mapper__=mapper, **kwargs)

    return uc


def _configure_endpoint_cors(app: Flask, path: str, trigger_options: TriggerHttp):
    """Configure CORS for a specific endpoint based on trigger options."""
    if not trigger_options.allow_cors:
        return

    cors_config = {
        "methods": [trigger_options.method.upper()],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }

    if trigger_options.allowed_origins:
        cors_config["origins"] = trigger_options.allowed_origins
    else:
        cors_config["origins"] = "*"

    # Apply CORS specifically to this route
    CORS(app, resources={path: cors_config})


def _add_use_case(
    app: Flask,
    use_case_info: UseCaseInfo,
    trigger: TriggerInfo,
    use_case_function
):
    """Add a Flask route for a use case based on its HTTP trigger configuration."""
    if not isinstance(trigger.options, TriggerHttp):
        return

    method = trigger.options.method.upper()
    path = trigger.options.path.replace("{", "<").replace("}", ">")

    # Configure endpoint-specific CORS
    _configure_endpoint_cors(app, path, trigger.options)

    app.add_url_rule(
        path,
        endpoint=use_case_info.keyname,
        methods=[method],
        view_func=_use_case_factory(
            use_case_name=use_case_info.keyname,
            fn=use_case_function,
            mapper=trigger.options.mapper
        )
    )


def init_flask_app(
        path: Optional[str] = None,
        app: Optional[Flask] = None,
        *,
        encoding: str = "utf-8",
        secret_key: Optional[str] = None,
        jwt_secret_key: Optional[str] = None,
        use_case_src: Optional[str] = "use_cases"
    ) -> Flask:
    """Initialize a Flask application based on service metadata with per-endpoint CORS.

    Parameters
    ----------
    path : str, optional
        Path to service metadata file. If None, searches default locations.
    app : Flask, optional
        Existing Flask application instance to configure. If None, a new instance is created.
    encoding : str, default="utf-8"
        File encoding for metadata.
    secret_key : str, optional
        Flask secret key for session management.
    jwt_secret_key : str, optional
        Secret key for JWT authentication.
    use_case_src : str, default="use_cases"
        Python module path where use case implementations are located.

    Returns
    -------
    Flask
        Configured Flask application with routes for all HTTP-triggered use cases."""
    # Load service metadata
    service_info = read_service_metadata(path, encoding)

    # Initialize Flask app
    if app is None:
        app = Flask(service_info.name)

    # Configure security
    if secret_key is not None:
        app.config["SECRET_KEY"] = secret_key
    if jwt_secret_key is not None:
        app.config["JWT_SECRET_KEY"] = jwt_secret_key

    # Register use cases as Flask routes
    for use_case_info in service_info.use_cases.values():
        use_case_function = None

        for trigger in use_case_info.triggers:
            if trigger.type not in (TriggerEnum.HTTP, TriggerEnum.WEBSOCKET):
                continue

            if use_case_function is None:
                # Dynamically import use case implementation
                module = importlib.import_module(f"{use_case_src}.{use_case_info.keyname}")
                var = "_".join(
                    [i.upper() for i in re.sub(r"([A-Z])", r" \1", use_case_info.keyname).split()]
                )

                if hasattr(module, var):
                    use_case_function = getattr(module, var)
                    if use_case_function is not None and isinstance(trigger.options, TriggerHttp):
                        _add_use_case(app, use_case_info, trigger, use_case_function)
                else:
                    print(f"Use case implementation '{use_case_info}' not found", file=sys.stdout)

            elif isinstance(trigger.options, TriggerHttp):
                _add_use_case(app, use_case_info, trigger, use_case_function)

    return app
