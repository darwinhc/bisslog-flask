"""
Module for generating a Flask application boilerplate from Bisslog metadata and use case code.

This builder analyzes declared metadata (e.g., triggers) and discovered use case implementations,
and generates the corresponding Flask code—including HTTP routes, WebSocket endpoints, security
configuration, and runtime setup.

The generated code is returned as a full Python script and can be written to a file (e.g.,
`flask_app.py`).
"""
from typing import Optional, Callable
import json

from bisslog_schema import read_full_service_metadata
from bisslog_schema.eager_import_module_or_package import EagerImportModulePackage
from bisslog_schema.schema import UseCaseInfo, TriggerHttp, TriggerWebsocket
from bisslog_schema.setup import get_setup_metadata
from bisslog_schema.use_case_code_inspector.use_case_code_metadata import UseCaseCodeInfo, \
    UseCaseCodeInfoClass, UseCaseCodeInfoObject
from .static_python_construct_data import StaticPythonConstructData


class BuilderFlaskAppManager:
    """
    Flask application builder for Bisslog-based services.

    This class dynamically generates Flask code based on user-declared metadata and
    the implementation of use cases discovered in the source tree. It supports HTTP
    and WebSocket triggers, integrates runtime setup from decorators, and configures
    environment-based security.

    The result is a complete Flask application scaffold that can be directly executed
    or used as a starting point for further customization.
    """

    def __init__(self, eager_importer: Callable[[str], None]):
        self._eager_importer = eager_importer


    def _get_bisslog_setup(self, infra_path: Optional[str]) -> Optional[StaticPythonConstructData]:
        """
        Retrieves the Bisslog setup call for the 'flask' runtime, if defined.

        This inspects the global Bisslog configuration and returns the corresponding
        setup function call code for Flask.

        Returns
        -------
        Optional[StaticPythonConstructData]
            The setup code and imports, or None if no setup was declared.
        """
        self._eager_importer(infra_path)
        setup_metadata = get_setup_metadata()
        if setup_metadata is None:
            return None

        if setup_metadata.setup_function is not None:
            n_params = setup_metadata.setup_function.n_params
            if n_params == 0:
                build = f"{setup_metadata.setup_function.function_name}()"
            elif n_params == 1:
                build = f"{setup_metadata.setup_function.function_name}(\"flask\")"
            else:
                build = (f"{setup_metadata.setup_function.function_name}(\"flask\")"
                         "  # TODO: change this")
            return StaticPythonConstructData(
                importing={setup_metadata.setup_function.module:
                               {setup_metadata.setup_function.function_name}},
                build=build,
            )
        custom_runtime_setup = setup_metadata.runtime.get("flask", None)
        if custom_runtime_setup is not None:
            return StaticPythonConstructData(
                importing={custom_runtime_setup.module:
                               {custom_runtime_setup.function_name}},
                build=f"{custom_runtime_setup.function_name}()"
            )
        return None

    @staticmethod
    def _generate_security_code() -> StaticPythonConstructData:
        """
        Generates Flask configuration code for secret keys using environment variables.

        Returns
        -------
        StaticPythonConstructData
            Code that assigns `SECRET_KEY` and `JWT_SECRET_KEY` to the Flask app.
        """
        build = """
if "SECRET_KEY" in os.environ:
    app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
if "JWT_SECRET_KEY" in os.environ:
    app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
"""
        return StaticPythonConstructData(build=build)

    @staticmethod
    def _generate_use_case_code_build(use_case_code_info: UseCaseCodeInfo):
        """
        Prepares the use case callable to be used in HTTP or WebSocket routes.

        If the use case is a class, an instance is created. If it's an object, it's referenced.

        Parameters
        ----------
        use_case_code_info : UseCaseCodeInfo
            Static metadata about the use case implementation.

        Returns
        -------
        Tuple[str, StaticPythonConstructData]
            - Name of the callable reference (e.g., variable or instance).
            - Generated setup code and required imports.
        """
        importing = {"flask": {"request"}, "bisslog.utils.mapping": {"Mapper"}}
        starting_build = ""
        if isinstance(use_case_code_info, UseCaseCodeInfoClass):
            importing[use_case_code_info.module] = {use_case_code_info.class_name}
            uc_callable = f"{use_case_code_info.name}_uc"
            starting_build += f"{uc_callable} = {use_case_code_info.class_name}()"
        elif isinstance(use_case_code_info, UseCaseCodeInfoObject):
            importing[use_case_code_info.module] = {use_case_code_info.var_name}
            uc_callable = use_case_code_info.var_name
        else:
            raise ValueError("Unsupported UseCaseCodeInfo type")
        return uc_callable, StaticPythonConstructData(build=starting_build, importing=importing)

    @staticmethod
    def _generate_use_case_code_http_trigger(
            use_case_key: str, uc_callable: str, use_case_code_info: UseCaseCodeInfo,
            trigger_info: TriggerHttp, identifier: int) -> StaticPythonConstructData:
        """
        Generates the code for a use case with an HTTP trigger.

        Parameters
        ----------
        use_case_key : str
            Name used to identify the use case route.
        use_case_code_info : UseCaseCodeInfo
            Static code metadata for the specific use case.
        trigger_info : TriggerHttp
            Metadata of the HTTP trigger.

        Returns
        -------
        StaticPythonConstructData
            The generated code for the HTTP trigger.
        """
        starting_build = ""
        mapper_code_lines = []
        if trigger_info.mapper is not None:
            mapper_name = f"{use_case_code_info.name}_mapper_{identifier}"
            starting_build += (f"\n{mapper_name} = Mapper(name=\"{use_case_key}_mapper\", "
                               f"base={json.dumps(trigger_info.mapper)})")
            mapper_code_lines.append(f"""
    res_map = {mapper_name}.map({{
        "path_query": request.view_args or {{}},
        "body": request.get_json(silent=True) or {{}},
        "params": request.args.to_dict(),
        "headers": request.headers,
    }})""")
        method = trigger_info.method.upper()
        flask_path = (trigger_info.path or f"/{use_case_key}").replace("{", "<").replace("}", ">")
        handler_name = f"{use_case_key}_handler_{identifier}"

        lines = [
            f'@app.route("{flask_path}", methods=["{method}"])',
            f'def {handler_name}():',
        ]
        if not mapper_code_lines:
            lines.append("    kwargs = {}")
            lines.append("    kwargs.update(request.view_args or {})")
            lines.append("    kwargs.update(request.get_json(silent=True) or {})")
            lines.append("    kwargs.update(request.args.to_dict())")
            lines.append("    kwargs.update(dict(request.headers))")
            lines.append(f"    return {uc_callable}(**kwargs)\n")
        else:
            lines.extend(mapper_code_lines)
            lines.append(f'    return {uc_callable}(**res_map)\n')

        return StaticPythonConstructData(build=starting_build, body="\n".join(lines))

    @staticmethod
    def _generate_use_case_code_websocket_trigger(
            use_case_key: str,
            uc_callable: str,
            use_case_code_info: UseCaseCodeInfo,
            trigger_info: TriggerWebsocket,
            identifier: int
    ) -> StaticPythonConstructData:
        """
        Generates the code for a use case with a WebSocket trigger using flask-sock.

        Parameters
        ----------
        use_case_key : str
            The identifier of the use case.
        uc_callable : str
            The callable name to invoke.
        use_case_code_info : UseCaseCodeInfo
            Info about where the use case is defined.
        trigger_info : TriggerWebsocket
            Metadata describing the trigger.
        identifier : int
            An integer used to ensure uniqueness of function names.

        Returns
        -------
        StaticPythonConstructData
            Code and imports needed for WebSocket registration.
        """
        route_key = trigger_info.route_key or f"{use_case_key}.default"
        handler_name = f"{use_case_key}_ws_handler_{identifier}"
        mapper_decl = ""

        imports = {
            use_case_code_info.module: {use_case_code_info.name},
            "flask_sock": {"Sock"},
            "flask": {"request"},
            "bisslog.utils.mapping": {"Mapper"},
            "json": None
        }

        if trigger_info.mapper:
            mapper_var = f"{use_case_key}_ws_mapper_{identifier}"
            mapper_json = json.dumps(trigger_info.mapper)
            mapper_decl = (f'\n{mapper_var} = Mapper(name="{use_case_key}_ws_mapper",'
                           f' base={mapper_json})')

            mapper_code = f"""
            try:
                body = json.loads(data)
            except Exception:
                body = {{}}
            res_map = {mapper_var}.map({{
                "route_key": "{route_key}",
                "connection_id": request.headers.get("Sec-WebSocket-Key"),
                "headers": request.headers,
                "body": body
            }})
            response = {uc_callable}(**res_map)
    """

        else:
            # fallback: pass entire raw message
            mapper_code = f"""
            try:
                payload = json.loads(data)
            except Exception:
                payload = {{}}
            response = {uc_callable}(**payload)
    """

        build = f"""
    @sock.route("/ws/{route_key}")
    def {handler_name}(ws):
        while True:
            data = ws.receive()
            if data is None:
                break;  # Client disconnected
    {mapper_code}
            if response is not None:
                ws.send(response)
    """

        return StaticPythonConstructData(
            importing=imports,
            build=(mapper_decl + build)
        )

    def __call__(self,
                 metadata_file: Optional[str] = None,
                 use_cases_folder_path: Optional[str] = None,
                 infra_path: Optional[str] = None,
                 *,
                 encoding: str = "utf-8",
                 secret_key: Optional[str] = None,
                 jwt_secret_key: Optional[str] = None,
                 **kwargs) -> str:
        """
        Main entry point for generating the full Flask application code.

        This method orchestrates metadata loading, trigger processing, and Flask code generation
        (HTTP routes, WebSocket handlers, runtime setup, security config). The resulting app code
        is returned as a ready-to-write Python string.

        Parameters
        ----------
        metadata_file : str, optional
            Path to the YAML or JSON metadata file.
        use_cases_folder_path : str, optional
            Path to the folder where use case implementations are located.
        infra_path : str, optional
            Path to additional infrastructure or adapter code.
        encoding : str, default="utf-8"
            Encoding used to read the metadata file.
        secret_key : str, optional
            secret key for Flask configuration.
        jwt_secret_key : str, optional
            JWT secret key for Flask configuration.
        **kwargs
            Additional keyword arguments (currently unused).

        Returns
        -------
        str
            The complete Flask application source code as a string.
        """
        full_service_metadata = read_full_service_metadata(
            metadata_file=metadata_file,
            use_cases_folder_path=use_cases_folder_path,
            encoding=encoding
        )
        service_info = full_service_metadata.declared_metadata
        use_cases = full_service_metadata.discovered_use_cases

        res = StaticPythonConstructData(
            importing={"flask": {"Flask"}, "os": None},
            build="app = Flask(__name__)"
        )
        res += self._get_bisslog_setup(infra_path)

        res += self._generate_security_code()

        # Use cases
        for use_case_key in service_info.use_cases:
            use_case_info: UseCaseInfo = service_info.use_cases[use_case_key]
            use_case_code_info: UseCaseCodeInfo = use_cases[use_case_key]
            triggers_http = [t for t in use_case_info.triggers
                             if isinstance(t.options, TriggerHttp)]
            triggers_ws = [t for t in use_case_info.triggers
                           if isinstance(t.options, TriggerWebsocket)]
            triggers_flask = triggers_http + triggers_ws
            if len(triggers_flask) == 0:
                continue
            uc_callable, res_uc = self._generate_use_case_code_build(use_case_code_info)
            res += res_uc
            for i, trigger in enumerate(triggers_flask):
                if isinstance(trigger.options, TriggerHttp):
                    res += self._generate_use_case_code_http_trigger(
                        use_case_key, uc_callable, use_case_code_info, trigger.options, i
                    )
                elif isinstance(trigger.options, TriggerWebsocket):
                    res += self._generate_use_case_code_websocket_trigger(
                        use_case_key, uc_callable, use_case_code_info, trigger.options, i
                    )
        res += StaticPythonConstructData(body='\nif __name__ == "__main__":\n'
                                              '    app.run(debug=True, host="0.0.0.0")')
        return res.generate_boiler_plate_flask()


bisslog_flask_builder = BuilderFlaskAppManager(EagerImportModulePackage(("src.infra", "infra")))
