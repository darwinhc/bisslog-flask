import pytest
import sys
import os
from unittest.mock import patch, MagicMock
from bisslog_flask import cli as cli_module


@patch("bisslog_flask.cli.run")
@patch("argparse.ArgumentParser.parse_args")
def test_cli_runs_successfully(mock_parse_args, mock_run):
    # Arrange
    mock_args = MagicMock()
    mock_args.command = "run"
    mock_args.metadata_file = "metadata.yml"
    mock_args.use_cases_folder_path = "src/uc"
    mock_args.encoding = "utf-8"
    mock_args.secret_key = "secret"
    mock_args.infra_path = "infra"
    mock_args.jwt_secret_key = "jwt"
    mock_parse_args.return_value = mock_args

    # Act
    cli_module.main()

    # Assert
    mock_run.assert_called_once_with(
        metadata_file="metadata.yml",
        use_cases_folder_path="src/uc",
        infra_path="infra",
        encoding="utf-8",
        secret_key="secret",
        jwt_secret_key="jwt"
    )


@patch("bisslog_flask.cli.run", side_effect=Exception("boom"))
@patch("argparse.ArgumentParser.parse_args")
def test_cli_catches_exceptions(mock_parse_args, mock_run, capsys):
    # Arrange
    mock_args = MagicMock()
    mock_args.command = "run"
    mock_args.metadata_file = "metadata.yml"
    mock_args.use_cases_folder_path = "src/uc"
    mock_args.encoding = "utf-8"
    mock_args.secret_key = None
    mock_args.jwt_secret_key = None
    mock_parse_args.return_value = mock_args

    # Act
    with pytest.raises(SystemExit):
        cli_module.main()

    captured = capsys.readouterr()
    assert "boom" in captured.err


def test_project_root_inserted(monkeypatch):
    # Arrange
    test_dir = os.getcwd()
    monkeypatch.setattr("argparse.ArgumentParser.parse_args", lambda self: MagicMock(command="noop"))

    # Clean state
    if test_dir in sys.path:
        sys.path.remove(test_dir)

    # Act
    cli_module.main()

    # Assert
    assert test_dir in sys.path
