"""
CLI-compatible utility for generating a Flask application boilerplate from Bisslog metadata.

This module defines a function that reads service metadata and discovered use cases,
generates the corresponding Flask application source code, and writes it to a file.
It is intended to be used as part of a command-line interface or automation script
to scaffold ready-to-run Flask services.

The generated code supports HTTP and WebSocket routes, environment-based security
configuration, and respects the Bisslog runtime setup defined via decorators.
"""
from typing import Optional
from ...builder.builder_flask_app_manager import bisslog_flask_builder

def build_boiler_plate_flask(
        metadata_file: Optional[str] = None,
        use_cases_folder_path: Optional[str] = None,
        infra_path: Optional[str] = None,
        encoding: str = "utf-8",
        target_filename: str = "flask_app.py"
):
    """
    Generates a Flask application boilerplate file from Bisslog metadata and use case code.

    This function loads the service metadata and associated use cases, builds the Flask
    application source code dynamically, and writes it to a Python file (e.g., `flask_app.py`).
    The generated app includes route registration, security setup, and optional WebSocket support.

    Parameters
    ----------
    metadata_file : str, optional
        Path to the YAML or JSON metadata file describing the service.
    use_cases_folder_path : str, optional
        Path to the folder where the use case implementations are located.
    infra_path : str, optional
        Path to the folder where infrastructure components (e.g., adapters) are defined.
    encoding : str, default="utf-8"
        The file encoding to use when reading and writing files.
    target_filename : str, default="flask_app.py"
        The output filename where the Flask boilerplate code will be written.

    Returns
    -------
    None
        This function writes the generated Flask app code directly to the specified file.
    """
    flask_boiler_plate_string = bisslog_flask_builder(
        metadata_file=metadata_file,
        use_cases_folder_path=use_cases_folder_path,
        infra_path=infra_path,
        encoding=encoding
    )

    with open(target_filename, "w", encoding=encoding) as f:
        f.write(flask_boiler_plate_string)
