from unittest.mock import patch, MagicMock


@patch("bisslog_flask.cli.commands.run.BisslogFlask")
def test_run_invokes_flask_run(mock_bisslog_flask):
    # Arrange
    fake_app = MagicMock()
    mock_bisslog_flask.return_value = fake_app

    from bisslog_flask.cli.commands.run import run

    # Act
    run(
        metadata_file="metadata.yml",
        use_cases_folder_path="src/use_cases",
        encoding="utf-16",
        secret_key="super-secret",
        jwt_secret_key="jwt-secret"
    )

    # Assert
    mock_bisslog_flask.assert_called_once_with(
        metadata_file="metadata.yml",
        use_cases_folder_path="src/use_cases",
        infra_folder_path=None,
        encoding="utf-16",
        secret_key="super-secret",
        jwt_secret_key="jwt-secret"
    )

    fake_app.run.assert_called_once()
