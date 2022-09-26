import pathlib
import tempfile

import pytest

from jupyter_compiler.analyzer import (
    analyze_notebook,
    convert_parameter_descriptor_to_jsonschema,
    convert_tableschema_descriptor_to_jsonschema,
    find_data_path,
    find_read_data_statements,
    get_notebook_hash,
    infer_data_schema,
    infer_data_schema_from_cell_output,
    infer_package_name,
    infer_parameter_name_and_value,
    read_notebook,
    scan_imports,
    scan_pragma_cells
)

RESOURCE_PATH = pathlib.Path(__file__).parent / "resources"


@pytest.fixture
def simple_notebook():
    path = RESOURCE_PATH / "simple.ipynb"
    return read_notebook(path)


def test_scan_imports(simple_notebook):
    import_statements = scan_imports(simple_notebook)
    assert import_statements == [
        "import pandas as pd",
        "from sklearn.linear_model import LogisticRegression",
        "import numpy as np",
        "from sklearn.preprocessing import LabelEncoder",
        "from sklearn.model_selection import train_test_split",
        "from sklearn.metrics import auc, classification_report, confusion_matrix, roc_curve",
    ]


def test_scan_pragama_cells(simple_notebook):
    pragma_label = "INPUT"
    pragma_cells = scan_pragma_cells(simple_notebook, pragma_label)
    assert len(pragma_cells) == 1

    pragma_label = "OUTPUT"
    pragma_cells = scan_pragma_cells(simple_notebook, pragma_label)
    assert len(pragma_cells) == 1

    pragma_label = "PARAMETER"
    pragma_cells = scan_pragma_cells(simple_notebook, pragma_label)
    assert len(pragma_cells) == 1


def test_infer_package_name():
    import_statement = "import pandas as pd"
    package_name = infer_package_name(import_statement)
    assert package_name == "pandas"

    import_statement = "from pandas import read_csv"
    package_name = infer_package_name(import_statement)
    assert package_name == "pandas"

    import_statement = "from pandas import read_csv as read_csv"
    package_name = infer_package_name(import_statement)
    assert package_name == "pandas"

    import_statement = "import os"
    package_name = infer_package_name(import_statement)
    assert package_name is None

    import_statement = "from sklearn.metrics import accuracy_score"
    package_name = infer_package_name(import_statement)
    assert package_name == "sklearn"

    import_statement = "from sklearn.metrics import accuracy_score as acc"
    package_name = infer_package_name(import_statement)
    assert package_name == "sklearn"


def test_find_read_data_statements():
    cell = """
df = pd.read_csv("data.csv")
    """

    statements = find_read_data_statements(cell)
    assert statements == ['pd.read_csv("data.csv")']

    cell = """
df = pd.read_csv("data.csv")

df2 = pd.read_csv("data2.csv")
    """

    statements = find_read_data_statements(cell)
    assert statements == ['pd.read_csv("data.csv")', 'pd.read_csv("data2.csv")']

    cell = """
# this is a comment
df = pd.read_csv("data.csv")
    """

    statements = find_read_data_statements(cell)
    assert statements == ['pd.read_csv("data.csv")']

    cell = """
df = pandas.read_csv("data.csv")
    """

    statements = find_read_data_statements(cell)
    assert statements == ['pandas.read_csv("data.csv")']

    cell = """
df = pd.read_excel("data.xlsx")
    """

    statements = find_read_data_statements(cell)
    assert statements == ['pd.read_excel("data.xlsx")']

    cell = """
df = pd.read_excel("data.xlsx", sheet_name="Sheet1")
    """

    statements = find_read_data_statements(cell)
    assert statements == ['pd.read_excel("data.xlsx", sheet_name="Sheet1")']

    cell = """
df = pd.read_table("data.txt")
    """

    statements = find_read_data_statements(cell)
    assert statements == ['pd.read_table("data.txt")']

    cell = """
pd.read_json("data.json")
    """
    statements = find_read_data_statements(cell)
    assert statements == ['pd.read_json("data.json")']

    cell = """
with open("data.csv") as f:
    pd.read_csv(f)
    """

    statements = find_read_data_statements(cell)
    assert statements == ["pd.read_csv(f)"]

    cell = """
pd.read_csv(f)
    """

    statements = find_read_data_statements(cell)
    assert statements == ["pd.read_csv(f)"]


def test_infer_parameters():
    cell = """
a = 1
b = "hello"
c : int = 2
d = 2.0
f = False
    """

    parameters = infer_parameter_name_and_value(cell)
    assert parameters == [
        {"name": "a", "type": "int", "default": 1},
        {"name": "b", "type": "str", "default": "hello"},
        {"name": "c", "type": "int", "default": 2},
        {"name": "d", "type": "float", "default": 2.0},
        {"name": "f", "type": "bool", "default": False},
    ]

    # composite types
    cell = """
a = [1, 2, 3]
b = {"a": 1, "b": 2}
c = ["hello", "world"]
d: List[int] = [1, 2, 3]
e: Dict[str, int] = {"a": 1, "b": 2}
f: List[str] = ["hello", "world"]
g: list[int] = [1, 2, 3]
"""

    parameters = infer_parameter_name_and_value(cell)
    assert parameters == [
        {"name": "a", "type": "list[int]", "default": [1, 2, 3]},
        {"name": "b", "type": "dict[str, int]", "default": {"a": 1, "b": 2}},
        {"name": "c", "type": "list[str]", "default": ["hello", "world"]},
        {"name": "d", "type": "list[int]", "default": [1, 2, 3]},
        {"name": "e", "type": "dict[str, int]", "default": {"a": 1, "b": 2}},
        {"name": "f", "type": "list[str]", "default": ["hello", "world"]},
        {"name": "g", "type": "list[int]", "default": [1, 2, 3]},
    ]

    # unknown composite types
    cell = """
a = []
"""

    parameters = infer_parameter_name_and_value(cell)
    assert parameters == [
        {"name": "a", "type": "list[unknown]", "default": []},
    ]

    # unsupported types
    cell = """
a = set([])
"""
    # excpected to raise a ValueError("Unknown type: set")
    with pytest.raises(ValueError, match="Function call is not supported"):
        infer_parameter_name_and_value(cell)

    cell = """
a = {1, 2, 3}
    """

    # excpected to raise a ValueError("Unknown type: set")
    with pytest.raises(ValueError, match="Unknown type: set"):
        infer_parameter_name_and_value(cell)

    cell = """
a = SomeClass()
"""

    # excpected to raise a ValueError("Unknown type: SomeClass")
    with pytest.raises(ValueError, match="Function call is not supported"):
        infer_parameter_name_and_value(cell)


def test_notebook_hash(simple_notebook):
    notebook_hash = get_notebook_hash(simple_notebook)
    assert notebook_hash

    # modify the notebook, the hash should change
    simple_notebook["cells"][0]["source"] = "a = 1"
    notebook_hash2 = get_notebook_hash(simple_notebook)

    assert notebook_hash != notebook_hash2


def test_find_data_path():
    statement = 'pd.read_csv("data.csv")'
    path = find_data_path(statement)
    assert path == "data.csv"

    statement = 'pd.read_csv("data.csv", header=None)'
    path = find_data_path(statement)
    assert path == "data.csv"

    statement = 'pandas.read_csv("data.csv")'
    path = find_data_path(statement)
    assert path == "data.csv"

    statement = 'pd.read_excel("data.xlsx")'
    path = find_data_path(statement)
    assert path == "data.xlsx"

    statement = 'pd.read_excel("data.xlsx", sheet_name="Sheet1")'
    path = find_data_path(statement)
    assert path == "data.xlsx"

    statement = 'pd.read_table("/some/path/to/data.txt")'
    path = find_data_path(statement)
    assert path == "/some/path/to/data.txt"


def test_infer_table_schema():
    iris_path = RESOURCE_PATH / "data" / "iris.csv"
    schema = infer_data_schema(iris_path)
    fields = schema["fields"]
    # assert fields equaility, but ignore the order
    assert fields == [
        {"name": "sepal.length", "type": "number", "format": "default"},
        {"name": "sepal.width", "type": "number", "format": "default"},
        {"name": "petal.length", "type": "number", "format": "default"},
        {"name": "petal.width", "type": "number", "format": "default"},
        {"name": "variety", "type": "string", "format": "default"},
    ]

    iris_few = RESOURCE_PATH / "data" / "iris_few.csv"
    schema = infer_data_schema(iris_few)

    fields = schema["fields"]
    # assert fields equaility, but ignore the order
    assert fields == [
        {"name": "sepal.length", "type": "number", "format": "default"},
        {"name": "sepal.width", "type": "number", "format": "default"},
        {"name": "petal.length", "type": "number", "format": "default"},
        {"name": "petal.width", "type": "number", "format": "default"},
        {"name": "variety", "type": "string", "format": "default"},
    ]

    simple = RESOURCE_PATH / "data" / "simple.csv"
    schema = infer_data_schema(simple)

    fields = schema["fields"]
    # assert fields equaility, but ignore the order
    assert fields == [
        {"name": "a", "type": "integer", "format": "default"},
        {"name": "b", "type": "integer", "format": "default"},
        {"name": "c", "type": "integer", "format": "default"},
    ]


def test_infer_output_schema(simple_notebook):
    # find the cell with comment "# PRAGMA OUTPUT"
    cells = scan_pragma_cells(simple_notebook, "OUTPUT")
    assert len(cells) == 1

    cell = cells[0]
    schema = infer_data_schema_from_cell_output(cell)
    fields = schema["fields"]
    assert fields == [
        {"name": "y_pred", "type": "integer", "format": "default"},
        {"name": "y_true", "type": "integer", "format": "default"},
        {"name": "sepal_length", "type": "number", "format": "default"},
        {"name": "sepal_width", "type": "number", "format": "default"},
        {"name": "petal_length", "type": "number", "format": "default"},
        {"name": "petal_width", "type": "number", "format": "default"},
    ]


def test_convert_tableschema_to_json_schema():
    tableschema_descriptor = {
        "fields": [
            {"name": "a", "type": "integer", "format": "default"},
            {"name": "b", "type": "integer", "format": "default"},
            {"name": "c", "type": "integer", "format": "default"},
        ]
    }

    json_schema = convert_tableschema_descriptor_to_jsonschema(tableschema_descriptor)
    assert json_schema == {
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "integer"},
            "c": {"type": "integer"},
        },
    }


def test_convert_parameter_descriptor_to_json_schema():
    parameter_descriptor = [
        {"name": "a", "type": "int", "default": 1},
        {"name": "b", "type": "float", "default": 2.0},
        {"name": "c", "type": "str", "default": "3"},
        {"name": "d", "type": "bool", "default": True},
    ]

    jsonschema = convert_parameter_descriptor_to_jsonschema(parameter_descriptor)
    assert jsonschema == {
        "type": "object",
        "properties": {
            "a": {"type": "integer", "default": 1},
            "b": {"type": "number", "default": 2.0},
            "c": {"type": "string", "default": "3"},
            "d": {"type": "boolean", "default": True},
        },
    }

    # composite type
    parameter_descriptor = [
        {"name": "a", "type": "int", "default": 1},
        {"name": "b", "type": "float", "default": 2.0},
        {"name": "c", "type": "str", "default": "3"},
        {"name": "d", "type": "List[int]", "default": [1, 2, 3]},
    ]

    with pytest.raises(ValueError):
        convert_parameter_descriptor_to_jsonschema(parameter_descriptor)


def test_analyze():
    notebook_path = RESOURCE_PATH / "simple.ipynb"
    result = analyze_notebook(notebook_path)
    assert set(result["packages"]) == set(
        [
            "pandas",
            "numpy",
            "sklearn",
        ]
    )

    assert result["parameter_schema"] == {
        "title": "Parameters",
        "type": "object",
        "properties": {
            "penalty": {"type": "string", "default": "l2"},
            "dual": {"type": "boolean", "default": False},
        },
    }

    assert result["input_schema"] == [
        {
            "title": "iris_csv",
            "type": "object",
            "_mount_path": (RESOURCE_PATH / "data" / "iris.csv").absolute().as_posix(),
            "properties": {
                "sepal.length": {"type": "number"},
                "sepal.width": {"type": "number"},
                "petal.length": {"type": "number"},
                "petal.width": {"type": "number"},
                "variety": {"type": "string"},
            },
        },
    ]

    assert result["output_schema"] == [
        {
            "title": "pd_concat_df_pred_X_test_axis_1_",
            "type": "object",
            "properties": {
                "y_pred": {"type": "integer"},
                "y_true": {"type": "integer"},
                "sepal_length": {"type": "number"},
                "sepal_width": {"type": "number"},
                "petal_length": {"type": "number"},
                "petal_width": {"type": "number"},
            },
        }
    ]

    assert result["hash"]
