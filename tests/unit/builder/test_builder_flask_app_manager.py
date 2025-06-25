import pytest
from unittest.mock import MagicMock, patch

from bisslog_schema.use_case_code_inspector.use_case_code_metadata import UseCaseCodeInfoClass, \
    UseCaseCodeInfoObject

from bisslog_flask.builder.builder_flask_app_manager import BuilderFlaskAppManager
from bisslog_flask.builder.static_python_construct_data import StaticPythonConstructData


@pytest.fixture
def sample_class_use_case():
    mock_info = UseCaseCodeInfoClass("my_use_case_cls", "docs", "my_module", "MyUseCase")
    return mock_info


@pytest.fixture
def sample_object_use_case():
    mock_info = UseCaseCodeInfoObject("my_use_case", "docs", "my_module", "my_use_case")
    return mock_info


def test_generate_security_code():
    result = BuilderFlaskAppManager._generate_security_code()
    assert isinstance(result, StaticPythonConstructData)
    assert "SECRET_KEY" in result.build
    assert "JWT_SECRET_KEY" in result.build


def test_generate_use_case_code_build_class(sample_class_use_case):
    uc_name, code_data = BuilderFlaskAppManager._generate_use_case_code_build(sample_class_use_case)
    assert uc_name == "my_use_case_cls_uc"
    assert "MyUseCase()" in code_data.build
    assert "my_module" in code_data.importing
    assert "MyUseCase" in code_data.importing["my_module"]


def test_generate_use_case_code_build_object(sample_object_use_case):
    uc_name, code_data = BuilderFlaskAppManager._generate_use_case_code_build(sample_object_use_case)
    assert uc_name == "my_use_case"
    assert "my_module" in code_data.importing
    assert "my_use_case" in code_data.importing["my_module"]


def test_generate_use_case_code_build_invalid_type():
    with pytest.raises(ValueError):
        BuilderFlaskAppManager._generate_use_case_code_build(246)


def test_get_bisslog_setup_none():
    with patch("bisslog_flask.builder.builder_flask_app_manager.get_setup_metadata", return_value=None):
        assert BuilderFlaskAppManager._get_bisslog_setup() is None


def test_get_bisslog_setup_with_setup_function():
    setup_mock = MagicMock()
    setup_mock.setup_function.n_params = 1
    setup_mock.setup_function.function_name = "init_app"
    setup_mock.setup_function.module = "config"
    setup_mock.runtime = {}
    with patch("bisslog_flask.builder.builder_flask_app_manager.get_setup_metadata", return_value=setup_mock):
        result = BuilderFlaskAppManager._get_bisslog_setup()
        assert "init_app(\"flask\")" in result.build
        assert "config" in result.importing
        assert "init_app" in result.importing["config"]


def test_get_bisslog_setup_with_runtime_only():
    setup_mock = MagicMock()
    setup_mock.setup_function = None
    runtime_info = MagicMock()
    runtime_info.function_name = "custom_setup"
    runtime_info.module = "custom_mod"
    setup_mock.runtime = {"flask": runtime_info}
    with patch("bisslog_flask.builder.builder_flask_app_manager.get_setup_metadata", return_value=setup_mock):
        result = BuilderFlaskAppManager._get_bisslog_setup()
        assert "custom_setup()" in result.build
        assert "custom_mod" in result.importing
        assert "custom_setup" in result.importing["custom_mod"]
