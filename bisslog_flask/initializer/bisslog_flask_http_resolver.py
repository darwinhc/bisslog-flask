"""
Flask HTTP resolver for Bisslog-based use case routing.

This module provides a class to dynamically register HTTP endpoints
in a Flask application using 'use case metadata'. It supports CORS configuration
and flexible request mapping using the Bisslog schema and Mapper.

Classes
-------
BisslogFlaskHttpResolver : Register HTTP routes for use cases based on metadata.

Dependencies
------------
- Flask
- flask_cors
- bisslog_schema
- bisslog.utils.mapping
"""
from copy import deepcopy
from typing import Callable, Optional, Dict

from flask import Flask, request, jsonify
try:
    from flask_cors import cross_origin
except ImportError:
    cross_origin = None
from bisslog.utils.mapping import Mapper
from bisslog_schema.schema import UseCaseInfo, TriggerHttp, TriggerInfo
from bisslog_schema.schema.triggers.trigger_mappable import TriggerMappable

from .bisslog_flask_resolver import BisslogFlaskResolver


class BisslogFlaskHttpResolver(BisslogFlaskResolver):
    """
    Flask HTTP resolver that dynamically registers use cases as routes based on metadata.

    This resolver wraps use case callables and maps request data accordingly,
    applying optional CORS configuration at the endpoint level.

    Inherits
    --------
    BisslogFlaskResolver
        Base resolver interface for trigger-based route binding.
    """

    @staticmethod
    def _lambda_fn(*args, fn, __mapper__: Optional[Mapper], **kwargs):
        """Wraps a use case function to extract and map request data.

        Parameters
        ----------
        *args : tuple
            Positional arguments passed by Flask (usually none).
        fn : Callable
            The actual use case function to invoke.
        __mapper__ : Optional[Mapper]
            Mapper to transform HTTP request parts into function arguments.
        **kwargs : dict
            Keyword arguments passed by Flask (URL params, etc.).

        Returns
        -------
        flask.Response
            A JSON response with the result of the use case.
        """
        if __mapper__ is None:
            more_kwargs = {}
            if request.method.lower() not in ["get"]:
                more_kwargs.update(request.get_json(silent=True) or {})
            return jsonify(fn(*args, **kwargs, **more_kwargs))

        res_map = __mapper__.map({
            "path_query": request.view_args or {},
            "body": request.get_json(silent=True) or {},
            "params": request.args.to_dict(),
            "headers": request.headers,
        })
        res = fn(**res_map)

        return jsonify(res)

    @staticmethod
    def _use_case_factory(
            use_case_name: str,
            fn: Callable,
            mapper: Optional[Dict[str, str]] = None,
            trigger: Optional[TriggerHttp] = None
    ):
        """
        Factory to produce a Flask view function with optional mapping and CORS.

        Parameters
        ----------
        use_case_name : str
            Unique name of the use case.
        fn : Callable
            The function to be wrapped and exposed via HTTP.
        mapper : dict, optional
            Mapping schema for request fields, if applicable.
        trigger : TriggerHttp, optional
            Trigger options used to configure CORS.

        Returns
        -------
        Callable
            A Flask-compatible view function.
        """
        use_case_fn_copy = deepcopy(fn)
        __mapper__ = Mapper(name=f"Mapper {use_case_name}", base=mapper) if mapper else None

        def uc(*args, **kwargs):
            return BisslogFlaskHttpResolver._lambda_fn(
                *args, fn=use_case_fn_copy, __mapper__=__mapper__, **kwargs
            )

        # Apply CORS dynamically if allowed
        if trigger and trigger.allow_cors:
            if cross_origin is None:
                raise ImportError("flask_cors is not installed, please install it")
            cors_kwargs = {
                "origins": trigger.allowed_origins or "*",
                "methods": [trigger.method.upper()],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True
            }
            return cross_origin(**cors_kwargs)(uc)

        return uc

    @classmethod
    def _add_use_case(cls, app: Flask, use_case_info: UseCaseInfo, trigger: TriggerInfo,
                      use_case_function):
        """
        Adds an HTTP endpoint to the Flask app for a given use case.

        Parameters
        ----------
        app : Flask
            The Flask application instance.
        use_case_info : UseCaseInfo
            Metadata describing the use case being added.
        trigger : TriggerInfo
            Metadata describing the trigger configuration (must be HTTP).
        use_case_function : Callable
            The use case logic to expose via HTTP.
        """
        if not isinstance(trigger.options, TriggerHttp):
            return

        method = trigger.options.method.upper()
        path = trigger.options.path.replace("{", "<").replace("}", ">")

        mapper = (
            trigger.options.mapper
            if isinstance(trigger.options, TriggerMappable)
            else None
        )
        app.add_url_rule(
            path,
            endpoint=use_case_info.keyname + " " + path,
            methods=[method],
            view_func=cls._use_case_factory(
                use_case_name=use_case_info.keyname,
                fn=use_case_function,
                mapper=mapper,
                trigger=trigger.options
            )
        )

    def __call__(self, app: Flask, use_case_info: UseCaseInfo,
                 trigger_info: TriggerInfo, use_case_callable: Callable, **kwargs):
        """Entry point to register a use case route using this resolver.

        Parameters
        ----------
        app : Flask
            The Flask app where the route will be registered.
        use_case_info : UseCaseInfo
            Metadata of the use case.
        trigger_info : TriggerInfo
            Trigger configuration for the route.
        use_case_callable : Callable
            The function to execute when the route is called.
        """
        self._add_use_case(app, use_case_info, trigger_info, use_case_callable)
