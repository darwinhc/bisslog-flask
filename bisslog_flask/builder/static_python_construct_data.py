"""
Module defining the response structure for AWS Lambda handler code generation.

This module provides a dataclass that encapsulates the components produced during
AWS Lambda handler code generation, including the function body, optional setup code,
and required import statements.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Set



@dataclass
class StaticPythonConstructData:
    """
    Response structure for generated AWS Lambda handler components.

    This dataclass represents the output of a code generator that produces AWS Lambda
    handler functions. It contains the function body as a string, any optional setup/build
    logic, and the necessary import statements grouped by module.

    Attributes
    ----------
    body : Optional[str]
        The body of the Lambda handler function as a Python code string.
    build : Optional[str]
        Optional setup or preconstruction code to include before the function body.
    importing : Dict[str, Set[str]]
        A mapping of module names to sets of symbols to import from them.

        This structure assumes simple `from module import symbol` semantics.

        Examples
        --------
        {
            "typing": {"List", "Optional"},
            "os": {"path", "environ"}
        }

    extra : Dict[str, Any]
        Optional extra data provided by the generator.
    """
    body: Optional[str] = None
    build: Optional[str] = None
    importing: Dict[str, Set[str]] = field(default_factory=dict)
    extra: Dict[str, Any] = field(default_factory=dict)

    def add_imports(self, new_imports: Dict[str, Set[str]]) -> None:
        """
        Adds new import statements to the existing import dictionary.

        Parameters
        ----------
        new_imports : Dict[str, Set[str]]
            A dictionary of module names and symbols to import.
        """
        for module, symbols in new_imports.items():
            if module not in self.importing:
                self.importing[module] = set()
            self.importing[module].update(symbols)

    @staticmethod
    def _generate_imports_string(imports: Dict[str, Set[str]]) -> str:
        """
        Generates a string representing import statements.

        Parameters
        ----------
        imports : Dict[str, Set[str]]
            A dictionary where keys are module names and values are sets of symbols.

        Returns
        -------
        str
            Formatted import statements, one per line.
        """
        return "\n".join(
            f"from {source} import {', '.join(sorted(var))}" if var else f"import {source}"
            for source, var in imports.items()
        )

    def generate_boiler_plate_flask(self) -> str:
        """
        Builds the final AWS Lambda handler code as a complete Python string.

        This includes import statements, any pre-construction logic, and
        the `lambda_handler` function definition.

        Returns
        -------
        str
            The full source code of the handler as a string.
        """
        imports_chunk = self._generate_imports_string(self.importing)
        sep = "\n" * 3
        return f"{imports_chunk}{sep}{self.build or ''}{sep}{self.body or ''}\n"

    def __add__(self, other: "StaticPythonConstructData") -> "StaticPythonConstructData":
        """
        Combine two AWSHandlerGenResponse objects by merging their fields.

        Parameters
        ----------
        other : StaticPythonConstructData
            Another response to merge.

        Returns
        -------
        StaticPythonConstructData
            A new instance with merged content.

        Raises
        ------
        NotImplementedError
            If `other` is not an instance of AWSHandlerGenResponse.
        """
        if not isinstance(other, StaticPythonConstructData):
            raise NotImplementedError

        merged_body = "\n".join(filter(None, [self.body, other.body])) or None
        merged_build = "\n".join(filter(None, [self.build, other.build])) or None

        merged_importing: Dict[str, Set[str]] = {}
        for module in set(self.importing) | set(other.importing):
            symbols_self = self.importing.get(module, set())
            symbols_other = other.importing.get(module, set())
            merged_importing[module] = symbols_self.union(symbols_other)

        return StaticPythonConstructData(
            body=merged_body,
            build=merged_build,
            importing=merged_importing,
            extra={}
        )

    def __iadd__(self, other: "StaticPythonConstructData") -> "StaticPythonConstructData":
        """
        In-place addition of another AWSHandlerGenResponse instance.

        Modifies the current instance by merging the fields from `other`.

        Parameters
        ----------
        other : StaticPythonConstructData
            The response to merge into this one.

        Returns
        -------
        StaticPythonConstructData
            The modified instance (`self`).

        Raises
        ------
        NotImplementedError
            If `other` is not an instance of AWSHandlerGenResponse.
        """
        if other is None:
            return self
        if not isinstance(other, StaticPythonConstructData):
            raise NotImplementedError

        self.body = "\n".join(filter(None, [self.body, other.body])) or None
        self.build = "\n".join(filter(None, [self.build, other.build])) or None

        for module, symbols in other.importing.items():
            if module not in self.importing:
                self.importing[module] = set()
            self.importing[module].update(symbols)

        self.extra = {}
        return self
