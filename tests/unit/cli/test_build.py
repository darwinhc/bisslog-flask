# test_cli_build_boilerplate.py

import builtins
import pytest
from unittest.mock import patch, mock_open
from bisslog_flask.cli.commands.build import build_boiler_plate_flask


@patch("bisslog_flask.cli.commands.build.bisslog_flask_builder")
@patch("builtins.open", new_callable=mock_open)
def test_build_boiler_plate_flask_writes_output(mock_file, mock_builder):
    mock_builder.return_value = "# Flask app generated code"

    build_boiler_plate_flask(
        metadata_file="meta.yaml",
        use_cases_folder_path="src/",
        infra_path="infra/",
        encoding="utf-8",
        target_filename="output.py"
    )

    mock_builder.assert_called_once_with(
        metadata_file="meta.yaml",
        use_cases_folder_path="src/",
        infra_path="infra/",
        encoding="utf-8"
    )

    mock_file.assert_called_once_with("output.py", "w", encoding="utf-8")
    handle = mock_file()
    handle.write.assert_called_once_with("# Flask app generated code")
