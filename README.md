# bisslog-flask

[![PyPI](https://img.shields.io/pypi/v/bisslog-flask)](https://pypi.org/project/bisslog-flask/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**bisslog-flask** is an extension of the Bisslog library to support processes with Flask.  
It enables dynamic HTTP and WebSocket route registration from use case metadata, allowing developers to build clean, modular, and metadata-driven APIs with minimal boilerplate.

Part of the Bisslog ecosystem, it is designed to work seamlessly with domain-centric architectures like Hexagonal or Clean Architecture.

---

## ✨ Features

- 🔁 Dynamic route registration for HTTP and WebSocket triggers
- 🧠 Metadata-driven setup – use YAML or JSON to declare your use cases
- 🔒 Automatic CORS per endpoint using `flask-cors`
- 🔌 Extensible resolver pattern – plug in your own processor
- ⚙️ Mapper integration – maps HTTP request parts to domain function arguments

---

## 📦 Installation

```bash
pip install bisslog-flask
```

---

## 🚀 Quickstart

### Programmatically

Use this approach if you want to configure the app before Bisslog touches it:

```python
from flask import Flask
from bisslog_flask import BisslogFlask

app = Flask(__name__)
BisslogFlask(
    metadata_file="metadata.yml",
    use_cases_folder_path="src/domain/use_cases",
    app=app
)

if __name__ == "__main__":
    app.run(debug=True)
```

Or use the factory version:

```python
from bisslog_flask import BisslogFlask

app = BisslogFlask(
    metadata_file="metadata.yml",
    use_cases_folder_path="src/domain/use_cases"
)

if __name__ == "__main__":
    app.run(debug=True)
```

---

## 🖥️ CLI Usage

You can also use the `bisslog_flask` CLI to run or generate a Flask app.

```bash
bisslog_flask run [--metadata-file FILE] [--use-cases-folder-path DIR]
                  [--infra-folder-path DIR] [--encoding ENC]
                  [--secret-key KEY] [--jwt-secret-key KEY]

bisslog_flask build [--metadata-file FILE] [--use-cases-folder-path DIR]
                    [--infra-folder-path DIR] [--encoding ENC]
                    [--target-filename FILE]
```

- `run`: Launches the Flask application from metadata.
- `build`: Generates a boilerplate Flask file (`flask_app.py` by default).

All options are optional. You can override defaults via CLI flags.

---

## 🔐 CORS Handling

CORS is applied only when `allow_cors: true` is specified in the trigger.

Fully dynamic: works even with Flask dynamic routes like `/users/<id>`.

Powered by `@cross_origin` from `flask-cors`.

---

## ✅ Requirements

- Python ≥ 3.7
- Flask ≥ 2.0
- bisslog-schema ≥ 0.0.3
- flask-cors
- (Optional) flask-sock if using WebSocket triggers

---

## 🧪 Testing Tip

You can test the generated Flask app directly with `app.test_client()` if using the programmatic interface:

```python
from bisslog_flask import BisslogFlask

def test_user_create():
    app = BisslogFlask(
        metadata_file="metadata.yml",
        use_cases_folder_path="src/use_cases"
    )
    client = app.test_client()
    response = client.post("/user", json={"name": "Ana", "email": "ana@example.com"})
    assert response.status_code == 200
```

If you're generating the code (boilerplate), you just need to test your use cases.

---

## 📜 License

This project is licensed under the MIT License.  
See the [LICENSE](LICENSE) file for details.