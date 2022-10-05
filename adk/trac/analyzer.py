import ast
import copy
import hashlib
import os
import pathlib
import re
import tempfile
from typing import List

import nbformat
import pandas as pd
import tableschema
from trac.constant import STDLIB_NAME


# read a notebook file using nbformat
def read_notebook(path):
    with open(path) as f:
        nb = nbformat.read(f, as_version=4)
    return nb


# scan through all cells in a notebook, find all import and from statements
def scan_imports(nb):
    imports = []
    for cell in nb.cells:
        if cell.cell_type == "code":
            for line in cell.source.splitlines():
                if line.startswith("import") or line.startswith("from"):
                    imports.append(line)
    return imports


# scan through all cells in a notebook, find all cells
# that starts with a comment line that contains the pragma_label
def scan_pragma_cells(nb, pragma_label):
    pragma_cells = []
    for cell in nb.cells:
        if cell.cell_type == "code":
            if cell.source.startswith(f"# PRAGMA {pragma_label}"):
                if pragma_label in cell.source:
                    pragma_cells.append(cell)
    return pragma_cells


def tag_pragma_cell(nb, pragma_label):
    """
    Tag a cell that starts with '# PRAGMA {pragma_label}' with the pragma_label
    """
    # plurize the pragma label
    pragma_label_plural = pragma_label + "s"

    for cell in nb.cells:
        if cell.cell_type == "code":
            if cell.source.startswith(f"# PRAGMA {pragma_label}"):
                if "tags" not in cell.metadata:
                    cell.metadata.tags = [pragma_label_plural.lower()]
                else:
                    # if the cell already have pragma tags, don't add it again
                    if pragma_label_plural.lower() not in cell.metadata.tags:
                        cell.metadata.tags.append(pragma_label_plural.lower())
    return nb


# infer the package name from an import statement,
# e.g. import pandas as pd -> pandas
# from pandas import read_csv -> pandas
# from sklearn.metrics import accuracy_score -> sklearn
# exclude standard library packages
def infer_package_name(import_statement):
    ast_tree = ast.parse(import_statement)
    if isinstance(ast_tree.body[0], ast.Import):
        package_name = ast_tree.body[0].names[0].name
    elif isinstance(ast_tree.body[0], ast.ImportFrom):
        package_name = ast_tree.body[0].module
    else:
        raise ValueError("Unknown import statement type: {}".format(import_statement))
    # exclude standard library packages
    if package_name in STDLIB_NAME:
        return None

    if "." in package_name:
        package_name = package_name.split(".")[0]
    return package_name


# find all data read statements in a cell
# e.g., pd.read_csv, pd.read_excel, pd.read_json, pd.read_html, pd.read_sql, pd.read_sql_query, pd.read_sql_table, pd.read_gbq, pd.read_hdf, pd.read_stata, pd.read_feather, pd.read_parquet, pd.read_msgpack, pd.read_pickle, pd.read_sas, pd.read_clipboard, pd.read_table
# e.g., pandas.read_csv, pandas.read_excel, pandas.read_json, pandas.read_html, pandas.read_sql, pandas.read_sql_query, pandas.read_sql_table, pandas.read_gbq, pandas.read_hdf, pandas.read_stata, pandas.read_feather, pandas.read_parquet, pandas.read_msgpack, pandas.read_pickle, pandas.read_sas, pandas.read_clipboard, pandas.read_table
# e.g., with open('data.csv') as f: pd.read_csv(f)
def find_read_data_statements(cell_source: str) -> List[str]:
    ast_tree = ast.parse(cell_source)
    statements = []
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                try:
                    if node.func.value.id in {
                        "pd",
                        "pandas",
                    } and node.func.attr.startswith("read_"):
                        # return the current node in source code form
                        statements.append(ast.get_source_segment(cell_source, node))
                except AttributeError:
                    pass
            elif isinstance(node.func, ast.Name):
                try:
                    if node.func.id in {"pd", "pandas"} and node.args[0].s.startswith(
                        "read_"
                    ):
                        # return the current node in source code form
                        statements.append(ast.get_source_segment(cell_source, node))
                except AttributeError:
                    pass

    return statements


def find_data_path(read_data_statement: str) -> str:
    """
    Given a read_data_statement, e.g., pd.read_csv("data.csv"), find the data path
    it reads in -> "data.csv"
    """
    ast_tree = ast.parse(read_data_statement)
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.value.id in {"pd", "pandas"} and node.func.attr.startswith(
                    "read_"
                ):
                    return node.args[0].s
            elif isinstance(node.func, ast.Name):
                if node.func.id in {"pd", "pandas"} and node.args[0].s.startswith(
                    "read_"
                ):
                    return node.args[0].s

    return None


def infer_data_schema(data_path):
    """
    Given a data path, e.g., "data.csv", infer the schema of the data
    Returns a json schema
    """
    if isinstance(data_path, pathlib.Path):
        data_path = str(data_path)
    if data_path.endswith(".csv"):
        schema = tableschema.infer(data_path)
        return schema
    else:
        raise ValueError(f"Unknown data format: {data_path}")


def infer_data_schema_from_cell_output(cell: nbformat.NotebookNode) -> dict:
    """
    Given a cell, check its output section, detect any html table, and infer its data schema
    Returns a json schema
    """
    if cell.cell_type != "code":
        return ValueError(f"Cell {cell} is not a code cell")

    if "outputs" not in cell:
        return None

    for output in cell.outputs:
        if output.output_type == "execute_result":
            if "data" in output:
                if "text/html" in output.data:
                    html = output.data["text/html"]
                    # find all tables, ignore the index column
                    tables = pd.read_html(html)
                    if len(tables) > 0:
                        # infer schema from the first table
                        table = tables[0]
                        # ignore the index column, and all columns with name "Unnamed: ..."
                        table = table.loc[:, ~table.columns.str.startswith("Unnamed")]
                        # write the table to a temporary file
                        with tempfile.NamedTemporaryFile(suffix=".csv") as f:
                            table.to_csv(f.name, index=False)
                            schema = infer_data_schema(f.name)
                        return schema
    return None


def convert_python_type_to_string_representation(python_type):
    """
    Convert a class type to a string representation.
    """
    if isinstance(python_type, type):
        return python_type.__name__
    else:
        return str(python_type)


def infer_list_elem_type(list_expr):
    if isinstance(list_expr, ast.List):
        if len(list_expr.elts) > 0:
            # type of the first element
            type_ = type(list_expr.elts[0].value)
            # convert type to string representation
            type_ = convert_python_type_to_string_representation(type_)
            return f"List[{type_}]"
        else:
            return "List[unknown]"
    return None


def infer_dict_key_value_type(dict_expr):
    if isinstance(dict_expr, ast.Dict):
        if len(dict_expr.keys) > 0:
            k_t, v_t = type(dict_expr.keys[0].value), type(dict_expr.values[0].value)
            k_t = convert_python_type_to_string_representation(k_t)
            v_t = convert_python_type_to_string_representation(v_t)
            return f"Dict[{k_t}, {v_t}]"
        else:
            return "Dict[unknown, unknown]"
    return None


# infer parameter name and values from a notebook cell
# e.g., a: int = 1 => {'name': 'a', 'type': 'int', 'value': 1}
# e.g., a = 1 => {'name': 'a', 'type': int, 'value': 1}
# e.g., b = 2.0 => {'name': 'b', 'type': float, 'value': 2.0}
# e.g., c = '3' => {'name': 'c', 'type': str, 'value': '3'}
# e.g., d = True => {'name': 'd', 'type': bool, 'value': True}
# e.g., b: str = "hello" => {'name': 'b', 'type': 'str', 'value': 'hello'}
# e.g., c: float = 1.0 => {'name': 'c', 'type': 'float', 'value': 1.0}
# e.g., d: bool = True => {'name': 'd', 'type': 'bool', 'value': True}
# e.g., e: list = [1, 2, 3] => {'name': 'e', 'type': 'list', 'value': [1, 2, 3]}
# e.g., f: dict = {'a': 1, 'b': 2} => {'name': 'f', 'type': 'dict', 'value': {'a': 1, 'b': 2}}
def infer_parameter_name_and_value(cell_source: str) -> dict:
    ast_tree = ast.parse(cell_source)
    parameters = []
    for node in ast.walk(ast_tree):
        if isinstance(node, ast.Assign):
            if isinstance(node.targets[0], ast.Name):
                name = node.targets[0].id
                # if value is a function call, e.g., set({}), set([]), set()
                if isinstance(node.value, ast.Call):
                    raise ValueError(
                        f"Function call is not supported for parameter {name}"
                    )
                value = ast.literal_eval(node.value)
                if isinstance(value, bool):
                    type_ = "bool"
                elif isinstance(value, int):
                    type_ = "int"
                elif isinstance(value, float):
                    type_ = "float"
                elif isinstance(value, str):
                    type_ = "str"
                elif isinstance(value, list):
                    # infer list element type
                    type_ = infer_list_elem_type(node.value)
                elif isinstance(value, dict):
                    type_ = infer_dict_key_value_type(node.value)
                else:
                    raise ValueError("Unknown type: {}".format(type(value).__name__))
                parameters.append({"name": name, "type": type_, "default": value})
            elif isinstance(node.targets[0], ast.Attribute):
                name = node.targets[0].attr
                value = ast.literal_eval(node.value)
                if isinstance(value, int):
                    type_ = "int"
                elif isinstance(value, float):
                    type_ = "float"
                elif isinstance(value, str):
                    type_ = "str"
                elif isinstance(value, bool):
                    type_ = "bool"
                elif isinstance(value, list):
                    type_ = infer_list_elem_type(node.value)
                elif isinstance(value, dict):
                    type_ = infer_dict_key_value_type(node.value)
                else:
                    raise ValueError("Unknown type: {}".format(type(value)))
                parameters.append({"name": name, "type": type_, "default": value})
            else:
                raise ValueError("Unknown type: {}".format(type(node.targets[0])))
        # if the statement is a type annotation
        elif isinstance(node, ast.AnnAssign):
            anno = node.annotation
            if isinstance(anno, ast.Name):
                type_ = anno.id
            elif isinstance(anno, ast.Subscript):
                type_ = ast.get_source_segment(cell_source, anno)
            else:
                raise ValueError("Unknown type: {}".format(type(anno)))
            if isinstance(node.target, ast.Name):
                name = node.target.id
                value = ast.literal_eval(node.value)
                parameters.append({"name": name, "type": type_, "default": value})
            elif isinstance(node.target, ast.Attribute):
                name = node.target.attr
                value = ast.literal_eval(node.value)
                parameters.append({"name": name, "type": type_, "default": value})
            else:
                raise ValueError("Unknown type: {}".format(type(node.target)))
    # convert type to lower case
    for p in parameters:
        p["type"] = p["type"].lower()

    return parameters


def get_notebook_hash(nb: nbformat.NotebookNode) -> str:
    """Get the hash of a notebook."""
    nb_copy = copy.deepcopy(nb)
    # clear the outputs of the notebook
    for cell in nb_copy.cells:
        if cell.cell_type == "code":
            cell.outputs = []
    # convert the notebook to a string
    nb_string = nbformat.writes(nb_copy)
    # get the hash of the notebook
    nb_hash = hashlib.sha256(nb_string.encode("utf-8")).hexdigest()
    return nb_hash


def convert_tableschema_descriptor_to_jsonschema(descriptor: dict) -> dict:
    """Convert a TableSchema descriptor to a JSONSchema descriptor."""
    jsonschema_descriptor = {"type": "object", "properties": {}}
    for field in descriptor["fields"]:
        jsonschema_descriptor["properties"][field["name"]] = {"type": field["type"]}
    return jsonschema_descriptor


def convert_parameter_descriptor_to_jsonschema(descriptor: dict) -> dict:
    """
    Convert a parameter descriptor to a JSONSchema descriptor.

    descriptor: {
        'name': 'a',
        'type': 'int',
        'default': 1
    }

    """
    jsonschema_descriptor = {"type": "object", "properties": {}}
    for parameter in descriptor:
        type_ = parameter["type"]
        # convert python type to jsonschema type
        if type_ == "int":
            type_ = "integer"
        elif type_ == "float":
            type_ = "number"
        elif type_ == "str":
            type_ = "string"
        elif type_ == "bool":
            type_ = "boolean"
        elif type_ == "list":
            type_ = "array"
            # TODO: we currently do not support the composite type
            raise ValueError("List type is not supported")
        elif type_ == "dict":
            type_ = "object"
            # TODO: we currently do not support the composite type
            raise ValueError("Dict type is not supported")
        else:
            raise ValueError(f"Unknown type: {type_}")

        jsonschema_descriptor["properties"][parameter["name"]] = {
            "type": type_,
            "default": parameter["default"],
        }
    return jsonschema_descriptor


def analyze_notebook(notebook_path, force=False) -> dict:
    """
    Analyze a notebook at notebook_path, generate its
    - input schema
    - parameter names and types
    - output schema
    - inferred requirements
    - hash

    Result
    """
    nb = nbformat.read(notebook_path, as_version=4)
    nb_hash = get_notebook_hash(nb)

    # check if the notebook has a metadata with convect field
    if "convect" in nb.metadata:
        convect_metadata = nb.metadata["convect"]
        # try to fetch the hash from convect metadata
        last_run_hash = convect_metadata.get("last_run_hash", None)
        if last_run_hash:
            # compare the hash of the notebook with the last run hash
            if nb_hash == last_run_hash and not force:
                # if the hash matches, we do not need to re-run the notebook
                return None

    # find all import statements
    import_statements = scan_imports(nb)
    packages = []
    for statement in import_statements:
        package_name = infer_package_name(statement)
        packages.append(package_name)
    # remove duplicates
    packages = list(set(packages))

    # get the input schema
    # find all cells with PRAGMA INPUT
    input_cells = scan_pragma_cells(nb, "INPUT")
    # for each input cell, get the schema
    input_schemas = []
    for cell in input_cells:
        # for each cell, find the data reading statements
        data_reading_statements = find_read_data_statements(cell.source)
        # for each statement, find the data path it reads from
        for statement in data_reading_statements:
            data_path = find_data_path(statement)
            # sanitize the data path as a valid dict key name
            file_name = os.path.basename(data_path).replace(".", "_")
            # data_path is relative to the notebook, unless it starts with /
            if not data_path.startswith("/"):
                # if the data path is relative, we need to get the notebook directory
                notebook_dir = os.path.dirname(notebook_path)
                readable_data_path = os.path.join(notebook_dir, data_path)
            else:
                readable_data_path = data_path

            # get the schema of the data
            schema = infer_data_schema(readable_data_path)
            # convert to jsonschema
            jsonschema = convert_tableschema_descriptor_to_jsonschema(schema)
            jsonschema["title"] = file_name
            jsonschema["_mount_path"] = data_path
            input_schemas.append(jsonschema)

    # get the parameter names and types
    # find all cells with PRAGMA PARAMETER
    parameter_schemas = []
    parameter_cells = scan_pragma_cells(nb, "PARAMETER")
    for cell in parameter_cells:
        schema = infer_parameter_name_and_value(cell.source)
        # convert to jsonschema
        jsonschema_descriptor = convert_parameter_descriptor_to_jsonschema(schema)
        parameter_schemas.append(jsonschema_descriptor)

    # combine multiple parameter schemas into one
    if len(parameter_schemas) > 1:
        properties_combined = {}
        for schema in parameter_schemas:
            properties_combined.update(schema["properties"])
        parameter_schemas = [{"type": "object", "properties": properties_combined}]
    parameter_schema = parameter_schemas[0]
    parameter_schema["title"] = "Parameters"

    # get the output schema
    # find all cells with PRAGMA OUTPUT
    output_cells = scan_pragma_cells(nb, "OUTPUT")
    # for each output cell, get the schema
    output_schemas = []
    for cell in output_cells:
        schema = infer_data_schema_from_cell_output(cell)
        # convert to jsonschema
        jsonschema = convert_tableschema_descriptor_to_jsonschema(schema)
        # use the variable name in the cell as the title
        key_name = cell.source.splitlines()[-1].strip()
        # sanitize the key name as a valid dict key name
        # replace none-alphanumeric characters with _
        key_name = re.sub(r"\W+", "_", key_name)
        jsonschema["title"] = key_name
        output_schemas.append(jsonschema)

    return {
        "input_schema": input_schemas,
        "parameter_schema": parameter_schema,
        "output_schema": output_schemas,
        "packages": packages,
        "hash": nb_hash,
    }
