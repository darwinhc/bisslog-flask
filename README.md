
# bisslog-flask

[![PyPI](https://img.shields.io/pypi/v/bisslog-flask)](https://pypi.org/project/bisslog-flask/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**bisslog-flask** is an extension of the bisslog library to support processes with Flask. It enables dynamic HTTP and WebSocket route registration from use case metadata, allowing developers to build clean, modular, and metadata-driven APIs with minimal boilerplate.

Part of the bisslog ecosystem, it is designed to work seamlessly with domain-centric architectures like Hexagonal or Clean Architecture.

## Features

- 🔁 Dynamic route registration for HTTP and WebSocket triggers

- 🧠 Metadata-driven setup – use YAML or JSON to declare your use cases

- 🔒 Automatic CORS per endpoint using flask-cors

- 🔌 Extensible resolver pattern – plug in your own processor

- ⚙️ Mapper integration – maps HTTP request parts to domain function arguments



## 📦 Installation

~~~shell
pip install bisslog-flask
~~~




## 🚀 Quickstart

### Programmatically

if you want to configure the app before bisslog touches it
~~~python
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
~~~

or

~~~python
from bisslog_flask import BisslogFlask

app = BisslogFlask(
    metadata_file="metadata.yml",
    use_cases_folder_path="src/domain/use_cases"
)

if __name__ == "__main__":
    app.run(debug=True)
~~~



## 🔧 How It Works

1. Loads metadata and discovers use case functions (or callables), then uses resolvers to register routes dynamically into a Flask app.


## 🔐 CORS Handling

CORS is applied only when allow_cors: true is specified in the trigger

Fully dynamic: works even with dynamic Flask routes like /users/<id>

Powered by `@cross_origin` from `flask-cors`


## ✅ Requirements

Python ≥ 3.7

Flask ≥ 2.0

bisslog-schema ≥ 0.0.3

flask-cors

(Optional) flask-socketio if using WebSocket triggers


## 🧪 Testing Tip

You can test the generated Flask app directly with `app.test_client()` if you take the programmatic way:

```python
from bisslog_flask import BisslogFlask

def test_user_create():
    app = BisslogFlask(metadata_file="metadata.yml", use_cases_folder_path="src/use_cases")
    client = app.test_client()
    response = client.post("/user", json={"name": "Ana", "email": "ana@example.com"})
    assert response.status_code == 200
```

Not generating code or using the programmatic way you just need to test your use cases.



## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.



