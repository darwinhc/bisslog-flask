"""
Command module to run a Flask application using Bisslog metadata.

This module provides a simple `run` function that initializes a Flask app
with use case metadata and launches the server. It is intended to be used
by the `bisslog_flask run` CLI command or directly from Python code.
"""

from typing import Optional

from bisslog_flask import BisslogFlask


def run(metadata_file: Optional[str] = None,
        use_cases_folder_path: Optional[str] = None,
        infra_path: Optional[str] = None,
        encoding: str = "utf-8",
        secret_key: Optional[str] = None,
        jwt_secret_key: Optional[str] = None):
    """
    Run a Flask application using metadata and use case source.

    This function creates and runs a Flask app configured through the
    BisslogFlask integration layer. It loads metadata definitions,
    applies HTTP and WebSocket use case resolvers, and starts the server.

    Parameters
    ----------
    metadata_file : str, optional
        Path to the metadata file (YAML or JSON) containing service and trigger definitions.
    use_cases_folder_path : str, optional
        Path to the folder where the use case implementation code is located.
    infra_path : str, optional
        Path to the folder containing infrastructure code (e.g., database, cache).
        This is not used in the current implementation but can be extended.
    encoding : str, optional
        Encoding used to read the metadata file (default is "utf-8").
    secret_key : str, optional
        Value to set as Flask's SECRET_KEY for session signing.
    jwt_secret_key : str, optional
        Value to set as Flask's JWT_SECRET_KEY for JWT-based authentication.
    """
    app = BisslogFlask(
        metadata_file=metadata_file,
        use_cases_folder_path=use_cases_folder_path,
        infra_path=infra_path,
        encoding=encoding,
        secret_key=secret_key,
        jwt_secret_key=jwt_secret_key
    )

    app.run()
