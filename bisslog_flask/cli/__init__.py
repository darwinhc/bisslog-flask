import os
import sys
import argparse
import traceback

from .commands.run import run
from .commands.build import build_boiler_plate_flask


def main():
    """
    Entry point for the `bisslog_flask` command-line interface.

    This function parses command-line arguments and executes the corresponding
    subcommand. Currently, it supports the `run` and `build` commands.

    Commands
    --------
    run
        Starts a Flask application based on provided metadata and use case folder.

    build
        Generates a Flask boilerplate app file from metadata and use cases.

    Raises
    ------
    Exception
        Any exception raised during command execution is caught and printed to stderr.
    """
    project_root = os.getcwd()

    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    parser = argparse.ArgumentParser(prog="bisslog_flask")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Define `run` command
    run_parser = subparsers.add_parser("run", help="Run a Flask app using metadata.")
    run_parser.add_argument("--metadata-file", type=str, default=None,
                            help="Path to metadata file (YAML or JSON).")
    run_parser.add_argument("--use-cases-folder-path", type=str, default=None,
                            help="Path to use case source folder.")
    run_parser.add_argument("--infra-path", type=str, default=None,
                            help="Path to infrastructure code folder (optional).")
    run_parser.add_argument("--encoding", type=str, default="utf-8",
                            help="File encoding (default: utf-8).")
    run_parser.add_argument("--secret-key", type=str,
                            help="Flask SECRET_KEY config value.")
    run_parser.add_argument("--jwt-secret-key", type=str,
                            help="Flask JWT_SECRET_KEY config value.")

    # Define `build` command
    build_parser = subparsers.add_parser("build",
                                         help="Generate a Flask app boilerplate file.")
    build_parser.add_argument("--metadata-file", type=str, default=None,
                              help="Path to metadata file (YAML or JSON).")
    build_parser.add_argument("--use-cases-folder-path", type=str, default=None,
                              help="Path to use case source folder.")
    build_parser.add_argument("--infra-path", type=str, default=None,
                              help="Path to infrastructure code folder (optional).")
    build_parser.add_argument("--encoding", type=str, default="utf-8",
                              help="File encoding (default: utf-8).")
    build_parser.add_argument("--target-filename", type=str, default="flask_app.py",
                              help="Filename to write the generated boilerplate (default: flask_app.py)")

    args = parser.parse_args()

    try:
        if args.command == "run":
            run(metadata_file=args.metadata_file,
                use_cases_folder_path=args.use_cases_folder_path,
                infra_path=args.infra_path,
                encoding=args.encoding,
                secret_key=args.secret_key,
                jwt_secret_key=args.jwt_secret_key)
        elif args.command == "build":
            build_boiler_plate_flask(
                metadata_file=args.metadata_file,
                use_cases_folder_path=args.use_cases_folder_path,
                infra_path=args.infra_path,
                encoding=args.encoding,
                target_filename=args.target_filename
            )
    except Exception as e:
        traceback.print_exc()
        print(e)
        sys.exit(1)
