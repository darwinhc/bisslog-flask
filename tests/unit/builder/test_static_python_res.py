
from bisslog_flask.builder.static_python_construct_data import StaticPythonConstructData


def test_add_imports_merges_modules_and_symbols():
    data = StaticPythonConstructData()
    data.add_imports({"os": {"environ"}, "typing": {"List"}})
    data.add_imports({"os": {"path"}, "typing": {"Optional"}})

    assert data.importing["os"] == {"environ", "path"}
    assert data.importing["typing"] == {"List", "Optional"}


def test_generate_imports_string_formats_correctly():
    imports = {
        "os": {"path", "environ"},
        "json": set()
    }
    result = StaticPythonConstructData._generate_imports_string(imports)
    expected_lines = {"from os import environ, path", "import json"}
    assert set(result.splitlines()) == expected_lines


def test_generate_boiler_plate_flask_structure():
    data = StaticPythonConstructData(
        body="def main(): pass",
        build="app = Flask(__name__)",
        importing={"flask": {"Flask"}}
    )
    output = data.generate_boiler_plate_flask()
    assert "from flask import Flask" in output
    assert "app = Flask(__name__)" in output
    assert "def main(): pass" in output


def test_add_operator_merges_components():
    a = StaticPythonConstructData(
        body="print('a')",
        build="init_a()",
        importing={"os": {"environ"}}
    )
    b = StaticPythonConstructData(
        body="print('b')",
        build="init_b()",
        importing={"os": {"path"}, "json": set()}
    )
    merged = a + b
    assert "print('a')" in merged.body
    assert "print('b')" in merged.body
    assert "init_a()" in merged.build
    assert "init_b()" in merged.build
    assert merged.importing["os"] == {"environ", "path"}
    assert "json" in merged.importing


def test_iadd_operator_merges_in_place():
    a = StaticPythonConstructData(
        body="first()",
        build="setup()",
        importing={"typing": {"Optional"}}
    )
    b = StaticPythonConstructData(
        body="second()",
        build="setup_b()",
        importing={"typing": {"List"}}
    )
    a += b
    assert "first()" in a.body
    assert "second()" in a.body
    assert "setup()" in a.build
    assert "setup_b()" in a.build
    assert a.importing["typing"] == {"Optional", "List"}
