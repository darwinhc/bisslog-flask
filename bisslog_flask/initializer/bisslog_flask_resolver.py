"""
Abstract base class for Bisslog Flask route resolvers.

This module defines a common interface for resolving use case routes
in a Flask application. Subclasses implement logic to register routes
based on different trigger types (e.g., HTTP, WebSocket).
"""
from abc import ABC, abstractmethod
from typing import Callable

from bisslog_schema.schema import UseCaseInfo, TriggerInfo

from flask import Flask


class BisslogFlaskResolver(ABC):
    """Abstract base class for registering use case routes in a Flask application.

    Implementations of this class handle the translation of trigger metadata
    into concrete route registration logic, such as for HTTP or WebSocket endpoints.

    Subclasses must implement the `__call__` method to perform the actual route binding."""

    @abstractmethod
    def __call__(self, app: Flask, use_case_info: UseCaseInfo,
                 trigger_info: TriggerInfo, use_case_callable: Callable, **kwargs) -> Callable:
        """
        Registers a use case route in a Flask app based on the given trigger.

        Parameters
        ----------
        app : Flask
            The Flask application instance where the route should be registered.
        use_case_info : UseCaseInfo
            Metadata describing the use case, including name and key.
        trigger_info : TriggerInfo
            Trigger metadata (e.g., HTTP, WebSocket) describing how the route is activated.
        use_case_callable : Callable
            The function or class instance that implements the use case logic.

        Raises
        ------
        NotImplementedError
            If the method is not implemented by a subclass.
        """
        raise NotImplementedError
